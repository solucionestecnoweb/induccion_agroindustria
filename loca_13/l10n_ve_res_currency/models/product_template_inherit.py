# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Productos(models.Model):
    _inherit = 'product.template'

    list_price2 = fields.Float(string="Precio de Venta en Divisas")
    list_price_comp = fields.Float(string="Precio Computado", compute='_compute_monto')
    moneda_divisa_venta = fields.Many2one("res.currency", string="Moneda del precio de venta en divisas",digits=(12, 2))#,required=True
    habilita_precio_div = fields.Boolean(default=False)

    @api.onchange('list_price2','moneda_divisa_venta','habilita_precio_div')
    def _compute_monto(self):
        self.list_price_comp=0
        self.list_price=0