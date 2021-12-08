# # -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, ValidationError
import openerp.addons.decimal_precision as dp
import logging

import io
from io import BytesIO
from io import StringIO

import xlsxwriter
import shutil
import base64
import csv

import urllib.request

import requests

_logger = logging.getLogger(__name__)

class EstadoCuenta(models.TransientModel):
    _name = 'wizard.estado.cuenta'

    date_from = fields.Date(string='Fecha desde', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Fecha hasta', default=lambda *a:(datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)
    saldo_uds=fields.Float(compute='_compute_saldo')
    saldo_bs=fields.Float()
    line  = fields.Many2many(comodel_name='resumen.estado.cuenta', string='Lineas')

    def _compute_saldo(self):
        valor_uds=0
        valor_bs=0
        cursor = self.env['account.ext.payment'].search([('state','=','paid')])
        if cursor:
            for rec in cursor:
                valor_uds=valor_uds+rec.monto_signed_uds
                valor_bs=valor_uds+rec.monto_signed
        self.saldo_uds=valor_uds
        self.saldo_bs=valor_bs

    def float_format2(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result

    def formato_fecha(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def action_generate_estado(self):
        acom_bs=0
        acom_uds=0
        t=self.env['resumen.estado.cuenta']
        d=t.search([])
        d.unlink()
        cursor_resumen = self.env['account.ext.payment'].search([
            ('fecha','>=',self.date_from),
            ('fecha','<=',self.date_to),
            ('state','=','paid'),
            ])
        if not cursor_resumen:
            raise UserError(_('No hay nada que reportar en esta fecha'))
        else:
            for det in cursor_resumen:
                values={
                'fecha':det.fecha,
                'referencia':det.name,
                'monto_uds':det.monto_signed_uds,
                'monto_bs':det.monto_signed,
                'tipo':det.tipo,
                'descripcion':det.doc_ext_order_id,
                }
                pdf_id = t.create(values)
                acom_uds=acom_uds+det.monto_signed_uds
                acom_bs=acom_bs+det.monto_signed
            self.line = self.env['resumen.estado.cuenta'].search([])
            self.saldo_uds=acom_uds
            self.saldo_bs=acom_bs
        return {'type': 'ir.actions.report','report_name': 'ext_caja_chica.libro_resumen_cuenta','report_type':"qweb-pdf"}


class ResumenEstadoCuenta(models.Model):
    _name = "resumen.estado.cuenta"

    fecha=fields.Datetime()
    referencia=fields.Char()
    descripcion=fields.Char()
    tipo=fields.Char(string="Débito/Crédito")
    monto_uds=fields.Float()
    monto_bs=fields.Float()

    def formato_fecha2(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def nb_tipo(self,valor):
        if valor=="egress":
            nb="Débito"
        if valor=="entry":
            nb="Crédito"
        return nb

    def float_format(self,valor):
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result