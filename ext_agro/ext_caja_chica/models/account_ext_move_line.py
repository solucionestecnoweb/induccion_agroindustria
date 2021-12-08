# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields,models,api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class AccountExtMoveLine(models.Model):
    _name = 'account.ext.move.line'

    fecha=fields.Datetime()
    referencia=fields.Char()
    descripcion=fields.Char()
    credit=fields.Float()
    debit=fields.Float()
    monto=fields.Float()
    saldo=fields.Float()
    monto_signed=fields.Float()
    saldo_signed=fields.Float()
    sale_ext_order_id=fields.Many2one('sale.ext.order')
    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)
    state = fields.Selection([('draft', 'Borrador'),('posted', 'Publicado')], readonly=True, default='draft', string="Status")


class AccountExtPayment(models.Model):
    _name = 'account.ext.payment'

    name=fields.Char(default="/", string="Nro Transacción")
    monto=fields.Monetary()
    monto_signed=fields.Float()
    monto_signed_uds=fields.Float()
    #currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id.id,string="Moneda de pago")
    currency_id = fields.Many2one('res.currency',default=2,string="Moneda de pago")
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)
    state = fields.Selection([('draft', 'Borrador'),('paid', 'Pagado')], readonly=True, default='draft', string="Status")
    account_journal_id = fields.Many2one('account.journal',string="Diario")
    fecha=fields.Datetime(default=lambda *a:(datetime.now().strftime('%Y-%m-%d'))
    sale_ext_order_id=fields.Many2one('sale.ext.order',string="Doc Venta")
    purchase_ext_order_id=fields.Many2one('purchase.ext.order',string="Doc Compra")
    doc_ext_order_id=fields.Char(compute='_compute_documento')
    tasa=fields.Float()
    monto_pendiente=fields.Float(compute='_compute_monto_pendiente')
    moneda_venta=fields.Many2one('res.currency',string="Moneda doc venta")
    cliente_id=fields.Many2one('res.partner')
    tipo = fields.Selection([('entry','Ingreso'),('egress','Egreso')])


    def _compute_documento(self):
        for selff in self:
            if selff.tipo=="egress":
                if selff.purchase_ext_order_id:
                    selff.doc_ext_order_id=selff.purchase_ext_order_id.name
                else:
                    selff.doc_ext_order_id="Retiro Directo"
            if selff.tipo=="entry":
                if selff.sale_ext_order_id:
                    selff.doc_ext_order_id=selff.sale_ext_order_id.name
                else:
                    selff.doc_ext_order_id="Deposito Directo"


    def action_register_ext_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        #raise UserError(_('valor=%s')%active_ids[0])
        #self.sale_ext_order_id=active_ids[0]
        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.ext.payment',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref('ext_caja_chica.vista_from_pago_cli').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    #@api.model
    @api.onchange('company_id')
    def default_nro_doc(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        #raise UserError(_('valorxxx=%s')%active_ids[0])
        if active_ids:
            valida_1=self.env['sale.ext.order'].search([('id','=',active_ids[0])])
            valida_2=self.env['purchase.ext.order'].search([('id','=',active_ids[0])])
            if valida_1:
                self.sale_ext_order_id=active_ids[0]
            if valida_2:
                self.purchase_ext_order_id=active_ids[0]


    @api.onchange('purchase_ext_order_id','sale_ext_order_id')
    def _compute_monto_pendiente(self):
        for rec in self:
            if rec.purchase_ext_order_id:
                rec.monto_pendiente=rec.purchase_ext_order_id.total_adeudado
                rec.moneda_venta=rec.purchase_ext_order_id.currency_id.id
                rec.account_journal_id=rec.purchase_ext_order_id.account_journal_id.id
                rec.tipo=rec.purchase_ext_order_id.tipo
            if rec.sale_ext_order_id:
                rec.monto_pendiente=rec.sale_ext_order_id.total_adeudado
                rec.moneda_venta=rec.sale_ext_order_id.currency_id.id
                rec.account_journal_id=rec.sale_ext_order_id.account_journal_id.id
                rec.tipo=rec.sale_ext_order_id.tipo
            if not rec.sale_ext_order_id and not rec.purchase_ext_order_id:
                rec.monto_pendiente=0
            
            #rec.currency_id=rec.sale_ext_order_id.currency_id.id
            #rec.tasa=rec.sale_ext_order_id.tasa
            #rec.monto=rec.sale_ext_order_id.total_adeudado


    def get_name(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_ve_cuenta_retencion_iva'''

        self.ensure_one()
        SEQUENCE_CODE = 'secuencia_pago_caja_dolar'
        company_id = self.env.company.id
        IrSequence = self.env['ir.sequence'].with_context(force_company=self.env.company.id)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': 'Pago Nro: ',
                'name': 'Secuencia Pago Caja Dolar %s' % self.env.company.name,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': self.env.company.id,#loca14
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    def pagar(self):
        if self.tasa=="0" or not self.tasa:
            raise UserError(_('Tiene que registrar un valor de tasa cambiaria'))
        #if not self.sale_ext_order_id and not self.purchase_ext_order_id:
            #raise UserError(_('Debe asociar un documento de venta / compra priemero'))
        self.state="paid"
        if self.name=="/":
            self.name=self.get_name()
        if self.tipo=="egress":
            signo=-1
        if self.tipo=="entry":
            signo=1
        if self.company_id.currency_id.id!=self.currency_id.id:
            self.monto_signed=signo*self.monto*self.tasa
            self.monto_signed_uds=signo*self.monto
        else:
            self.monto_signed=signo*self.monto
            self.monto_signed_uds=signo*self.monto/self.tasa
        if self.tipo=="entry":
            valor=self.sale_ext_order_id.total_adeudado
        if self.tipo=="egress":
            valor=self.purchase_ext_order_id.total_adeudado

        # Descuento cuanto la moneda de pago es igual a la moneda del registro de ventas
        if self.currency_id.id==self.moneda_venta.id:
            if self.tipo=="entry":
                self.sale_ext_order_id.total_adeudado=valor-self.monto
            if self.tipo=="egress":
                self.purchase_ext_order_id.total_adeudado=valor-self.monto
        # Descuento cuanto la moneda de pago es diferente a la moneda del registro de ventas
        if self.currency_id.id!=self.moneda_venta.id:
            if self.moneda_venta.id!=self.company_id.currency_id.id:
                if self.tipo=="entry":
                    self.sale_ext_order_id.total_adeudado=(valor-(self.monto/self.tasa))
                if self.tipo=="egress":
                    self.purchase_ext_order_id.total_adeudado=(valor-(self.monto/self.tasa))
            else:
                if self.tipo=="entry":
                    self.sale_ext_order_id.total_adeudado=(valor-(self.monto*self.tasa))
                if self.tipo=="egress":
                    self.purchase_ext_order_id.total_adeudado=(valor-(self.monto*self.tasa))
        # Cambia el status del documento de venta
        if self.tipo=="entry":
            if self.sale_ext_order_id.total_adeudado>0:
                self.sale_ext_order_id.state="partial _paid"
            if self.sale_ext_order_id.total_adeudado==0:
                self.sale_ext_order_id.state="paid"
        if self.tipo=="egress":
            if self.purchase_ext_order_id.total_adeudado>0:
                self.purchase_ext_order_id.state="partial _paid"
            if self.purchase_ext_order_id.total_adeudado==0:
                self.purchase_ext_order_id.state="paid"
        if self.tipo=="entry":
            busca=self.env['sale.ext.order'].search([('id','=',self.sale_ext_order_id.id)])
        if self.tipo=="egress":
            busca=self.env['purchase.ext.order'].search([('id','=',self.purchase_ext_order_id.id)])
        if busca:
            self.tipo=busca.tipo
            self.cliente_id=busca.cliente_id.id

    def cancel(self):
        self.state="draft"

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


