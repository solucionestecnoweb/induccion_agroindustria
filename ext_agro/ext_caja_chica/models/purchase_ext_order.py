# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields,models,api,_
import datetime
from odoo.exceptions import UserError, ValidationError

class Partners(models.Model):
    _inherit = 'account.journal'

    tipo_doc = fields.Selection([('nc', 'Nota de Credito'),('nb', 'Nota de Debito'),('fc','Factura fiscal'),('fnc','Factura No fiscal')])

class PurchaseExtOrder(models.Model):
    _name = 'purchase.ext.order'

    cliente_id = fields.Many2one('res.partner')
    date_pago=fields.Datetime()
    account_journal_id = fields.Many2one('account.journal')
    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id.id)
    line_ids = fields.One2many('purchase.ext.order.line', 'purchase_ext_id', string='Prestamos')
    total_base =fields.Monetary(string="Base Imponible",compute='_compute_base')
    total_impuesto = fields.Monetary(string="Impuesto",compute='_compute_impuesto')
    total = fields.Monetary(string="Total",compute='_compute_total')
    total_adeudado = fields.Monetary(string="Importe Adeudado")

    def _compute_base(self):
        acom=0
        for det in self.line_ids:
            acom=acom+det.sub_total
        self.total_base=acom

    def _compute_total(self):
        acom=0
        for det in self.line_ids:
            acom=acom+det.total
        self.total=acom

    def _compute_impuesto(self):
        acom=0
        for det in self.line_ids:
            acom=acom+(det.sub_total*det.tax_ids.amount/100)
        self.total_impuesto=acom

class PurchaseExtOrderLine(models.Model):
    _name = 'purchase.ext.order.line'

    purchase_ext_id = fields.Many2one('purchase.ext.order', string='Lineas de pedidos')
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
            selff.company_currency_id_aux=selff.purchase_ext_id.currency_id.id
            selff.company_currency_id=selff.company_currency_id_aux
