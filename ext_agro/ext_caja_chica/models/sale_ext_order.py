# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields,models,api,_
import datetime
from odoo.exceptions import UserError, ValidationError

class Partners(models.Model):
    _inherit = 'account.journal'

    tipo_doc = fields.Selection([('nc', 'Nota de Credito'),('nb', 'Nota de Debito'),('fc','Factura fiscal'),('fnc','Factura No fiscal')])

class SaleExtOrder(models.Model):
    _name = 'sale.ext.order'

    name = fields.Char(default="/")
    cliente_id = fields.Many2one('res.partner')
    date_pago=fields.Datetime()
    account_journal_id = fields.Many2one('account.journal')
    #currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id.id)
    currency_id = fields.Many2one('res.currency',default=2)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)
    line_ids = fields.One2many('sale.ext.order.line', 'sale_ext_id', string='Prestamos')
    tasa = fields.Float(default=1)
    total_base =fields.Monetary(string="Base Imponible",compute='_compute_base')
    total_impuesto = fields.Monetary(string="Impuesto",compute='_compute_impuesto')
    total = fields.Monetary(string="Total",compute='_compute_total')
    total_signed = fields.Monetary()
    total_signed_uds = fields.Monetary()
    total_adeudado = fields.Monetary(string="Importe Adeudado")
    state = fields.Selection([('draft', 'Borrador'), ('posted', 'Publicado'),('partial _paid', 'Parcialmente Pagado'),('paid', 'Totalmente Pagado')], readonly=True, default='draft', string="Status")
    tipo = fields.Char(default="entry")

    def _compute_base(self):
        acom=0
        for det in self.line_ids:
            acom=acom+det.sub_total
        self.total_base=acom

    def _compute_total(self):
        for selff in self:
            acom=0
            for det in selff.line_ids:
                acom=acom+det.total
            selff.total=acom
            if selff.company_id.currency_id.id!=selff.currency_id.id:
                selff.total_signed=acom*selff.tasa
                #selff.total_signed_uds=acom
            else: 
                selff.total_signed=acom
                #selff.total_signed_uds=acom*selff.tasa
            selff.total_signed_uds=selff.total_signed/selff.tasa

    def _compute_impuesto(self):
        acom=0
        for det in self.line_ids:
            acom=acom+(det.sub_total*det.tax_ids.amount/100)
        self.total_impuesto=acom

    def aprobar(self):
        self.state="posted"
        if self.name=="/":
            self.name=self.get_name()
        self.total_adeudado=self.total

    def cancel(self):
        self.state="draft"

    def get_name(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_ve_cuenta_retencion_iva'''

        self.ensure_one()
        SEQUENCE_CODE = 'secuencia_caja_dolar'+str(self.env.company.id)
        company_id = self.env.company.id
        IrSequence = self.env['ir.sequence'].with_context(force_company=self.env.company.id)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': 'Registro Nro: ',
                'name': 'Localización Venezolana Caja Dolar %s' % self.env.company.name,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': self.env.company.id,#loca14
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    def pagar(self):
        #raise UserError(_("id factura=%s")%self.id)
        return self.env['account.ext.payment']\
            .with_context(active_ids=self.ids, active_model='sale.ext.order', active_id=self.id)\
            .action_register_ext_payment()

    def doc_cedula(self,aux):
        #nro_doc=self.partner_id.vat
        busca_partner = self.env['res.partner'].search([('id','=',aux)])
        for det in busca_partner:
            tipo_doc=busca_partner.doc_type
            if busca_partner.vat:
                nro_doc=str(busca_partner.vat)
            else:
                nro_doc="00000000"
            tipo_doc=busca_partner.doc_type
        nro_doc=nro_doc.replace('V','')
        nro_doc=nro_doc.replace('v','')
        nro_doc=nro_doc.replace('E','')
        nro_doc=nro_doc.replace('e','')
        nro_doc=nro_doc.replace('G','')
        nro_doc=nro_doc.replace('g','')
        nro_doc=nro_doc.replace('J','')
        nro_doc=nro_doc.replace('j','')
        nro_doc=nro_doc.replace('P','')
        nro_doc=nro_doc.replace('p','')
        nro_doc=nro_doc.replace('-','')
        
        if tipo_doc=="v":
            tipo_doc="V"
        if tipo_doc=="e":
            tipo_doc="E"
        if tipo_doc=="g":
            tipo_doc="G"
        if tipo_doc=="j":
            tipo_doc="J"
        if tipo_doc=="p":
            tipo_doc="P"
        resultado=str(tipo_doc)+"-"+str(nro_doc)
        return resultado

    def formato_fecha(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result = "0,00"
        return result

    def fact_div(self,valor):
        resultado=valor
        return resultado

class SaleExtOrderLine(models.Model):
    _name = 'sale.ext.order.line'

    sale_ext_id = fields.Many2one('sale.ext.order', string='Lineas de pedidos')
    product_id = fields.Many2one('product.template')
    qty=fields.Float()
    precio_unit = fields.Float()
    sub_total = fields.Float(compute='_compute_sub_total')
    total = fields.Float(compute='_compute_total')
    #tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")
    tax_ids = fields.Many2one('account.tax', string='Impuesto', help="Taxes that apply on the base amount")
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company.id)
    company_currency_id_aux = fields.Many2one('res.currency',compute='_compute_currency')
    company_currency_id = fields.Many2one('res.currency')

    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result = "0,00"
        return result

    def fact_div_line(self,valor):
        valor_aux=0
        resultado=valor
        return resultado


    @api.depends('precio_unit','qty')
    def _compute_sub_total(self):
        for selff in self:
            resultado=selff.precio_unit*selff.qty
            selff.sub_total=resultado


    @api.depends('precio_unit','qty','tax_ids')
    def _compute_total(self):
        for selff in self:
            sub=selff.precio_unit*selff.qty
            resultado=(sub*selff.tax_ids.amount/100)+sub
            selff.total=resultado

    def _compute_currency(self):
        for selff in self:
            selff.company_currency_id_aux=selff.sale_ext_id.currency_id.id
            selff.company_currency_id=selff.company_currency_id_aux
