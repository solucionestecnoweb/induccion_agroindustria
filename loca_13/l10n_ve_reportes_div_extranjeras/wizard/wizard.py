from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
import logging

import io
from io import BytesIO

import xlsxwriter
import shutil
import base64
import csv
import xlwt
import xml.etree.ElementTree as ET

class ReporteMoneda(models.Model):
    _name = "reporte.moviextra.wizard.pdf"

    fecha_desde=fields.Date()
    fecha_hasta=fields.Date()
    account_id=fields.Many2one('account.account')
    name=fields.Char()
    total_deber=fields.Float()
    total_haber=fields.Float()

    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result

class WizardReport_2(models.TransientModel): # aqui declaro las variables del wizar que se usaran para el filtro del pdf
    _name = 'wizard.movi.extra'
    _description = "Mov de mon local a extranjera"

    date_from  = fields.Date('Date From', default=lambda *a:(datetime.now() - timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Date To', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))

    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)
    line  = fields.Many2many(comodel_name='reporte.moviextra.wizard.pdf', string='Lineas')
    currency_company_id=fields.Many2one('re.currency', default=lambda self: self.env.company.currency_id.id)
    moneda_id = fields.Many2one('res.currency',domain=lambda self:[('id', '!=',self.env.company.currency_id.id)])

    def rif(self,aux):
        #nro_doc=self.partner_id.vat
        busca_partner = self.env['res.partner'].search([('id','=',aux)])
        for det in busca_partner:
            tipo_doc=busca_partner.doc_type
            nro_doc=str(busca_partner.vat)
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
        if tipo_doc=="c":
            tipo_doc="C"
        resultado=str(tipo_doc)+"-"+str(nro_doc)
        return resultado

    def periodo(self,date):
        fecha = str(date)
        fecha_aux=fecha
        mes=fecha[5:7] 
        resultado=mes
        return resultado

    def formato_fecha(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

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



    def print_reporte_conversion(self):
        if not self.moneda_id.id:
            raise UserError(_('Debe seleccionar una moneda'))
        t=self.env['reporte.moviextra.wizard.pdf'].search([])
        w=self.env['wizard.movi.extra'].search([('id','!=',self.id)])
        t.unlink()
        w.unlink()
        cur_account=self.env['account.account'].search([('company_id','=',self.env.company.id)],order="code asc")
        for det_account in cur_account:
            acum_deber=0
            acum_haber=0
            cursor = self.env['account.move.line'].search([('date', '>=', self.date_from),('date','<=',self.date_to),('account_id','=',det_account.id),('parent_state','=','posted')])
            """if cursor:
                raise UserError(_('cursor = %s')%cursor)"""
            if cursor:
                for det in cursor:
                    acum_deber=acum_deber+self.conv_div_extranjera(det.debit,det)
                    acum_haber=acum_haber+self.conv_div_extranjera(det.credit,det)
                #raise UserError(_('lista_mov_line = %s')%acum_deber)
                values=({
                    'account_id':det_account.id,
                    'total_deber':acum_deber,
                    'total_haber':acum_haber,
                    'name':det_account.name,
                    'fecha_desde':self.date_from,
                    'fecha_hasta':self.date_to,
                    })
                diario_id = t.create(values)
        self.line=self.env['reporte.moviextra.wizard.pdf'].search([])
        return {'type': 'ir.actions.report','report_name': 'l10n_ve_reportes_div_extranjeras.reporte_mon_local_extranjera','report_type':"qweb-pdf"}
        #raise UserError(_('lista_mov_line = %s')%self.line)


    def conv_div_extranjera(self,valor,selff):
        #raise UserError(_('moneda compañia: %s')%selff.move_id.id)
        selff.move_id.currency_id.id
        fecha_contable_doc=selff.move_id.date
        monto_factura=selff.move_id.amount_total
        valor_aux=0
        #raise UserError(_('moneda compañia: %s')%self.company_id.currency_id.id)
        if selff.move_id.currency_id.id!=self.env.company.currency_id.id:#AQUI LA TRANSACCION FUE EN MONEDA EXTRANJERA 
            #raise UserError(_('Opcion 1'))
            tasa= self.env['account.move'].search([('id','=',selff.move_id.id)],order="id asc")
            for det_tasa in tasa:
                monto_nativo=det_tasa.amount_total_signed
                monto_extran=det_tasa.amount_total
                valor_aux=abs(monto_nativo/monto_extran)
            rate=round(valor_aux,3)  # LANTA
            #rate=round(valor_aux,2)  # ODOO SH
            resultado=valor/rate
        else: #AQUI LA TRANSACCION FUE EN MONEDA LOCAL 
            #raise UserError(_('Opcion 2'))
            tabla_move= self.env['account.move'].search([('id','=',selff.move_id.id)],order="id asc")
            for det_mov in tabla_move:
                tasa= self.env['res.currency.rate'].search([('currency_id','=',self.moneda_id.id),('name','<=',det_mov.date)],order="name asc")
                if not tasa:
                    raise UserError(_('No hay una tasa de conversion para esta moneda seleccionada para este rango de fecha'))
                for det_tasa in tasa:
                    if det_mov.date>=det_tasa.name:
                        valor_aux=det_tasa.rate
                rate=round(1/valor_aux,2)  # LANTA
                #rate=round(valor_aux,2)  # ODOO SH
                resultado=valor/rate
        return resultado