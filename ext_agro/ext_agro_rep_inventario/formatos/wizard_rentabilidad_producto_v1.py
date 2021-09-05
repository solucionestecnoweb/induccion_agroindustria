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

class ResumenMunicipalModelo3(models.Model):
    _name = "rentabilidad.producto.pdf"

    routing_id = fields.Many2one('mrp.routing')
    code = fields.Char()
    codigo = fields.Char()
    product_id = fields.Many2one('product.template')
    cantidad = fields.Float()
    ventas = fields.Float()
    costo = fields.Float()
    rentabilidad = fields.Float()
    utilidad = fields.Float()
   

    def float_format(self,valor):
        #valor=self.base_tax
        result="0,00"
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result


class WizardReport_3(models.TransientModel): # aqui declaro las variables del wizar que se usaran para el filtro del pdf
    _name = 'wizard.rentabilidad.producto'
    _description = "Resumen rentabilidad"

    date_from  = fields.Date('Date From', default=lambda *a:(datetime.now() - timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Date To', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_actual = fields.Date(default=lambda *a:datetime.now().strftime('%Y-%m-%d'))

    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    line  = fields.Many2many(comodel_name='rentabilidad.producto.pdf', string='Lineas')

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
        result="0,00"
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result


    def get_invoice(self):
        inventario_total=0
        t=self.env['rentabilidad.producto.pdf']
        d=t.search([])
        d.unlink()
        cursor_resumen = self.env['mrp.routing'].search([]) #('x_studio_ubicacion_final','=','si')
        #raise UserError(_('cursor_resumen: %s')%cursor_resumen)
        if cursor_resumen:
            for det in cursor_resumen:
                routing_id=det.id
                values={
                'routing_id':routing_id,
                'code':det.code,
                'codigo':"APP3",
                'product_id':41,
                'cantidad':300,
                'ventas':200,
                'costo':20,
                'rentabilidad':34,
                'utilidad':667,

                }
                pdf_id = t.create(values)
        #   temp = self.env['account.wizard.pdf.ventas'].search([])
        self.line = self.env['rentabilidad.producto.pdf'].search([])

    def total_inventario(self,id_location):
        total=0
        lista_quant=self.env['stock.quant'].search([('location_id','=',id_location)]) #('in_date','>=',self.date_from),('in_date','<=',self.date_to)
        if lista_quant:
            for dett in lista_quant:
                total=total+dett.quantity
        else:
          raise UserError(_('No hay datos que mostrar'))  
        return total

    def total_mortalidad(self,id_location):
        total=0
        lista_quant=self.env['stock.quant'].search([('location_id','=',id_location)])
        if lista_quant:
            for det in lista_quant:
                producto_id=det.product_id.id
                lista_scrap=self.env['stock.scrap'].search([('product_id','=',producto_id)]) # aqui se coloca filtro de fechas
                if lista_scrap:
                    for rec in lista_scrap:
                        total=total+rec.scrap_qty
        return total


    def print_resumen(self):
        #pass
        self.get_invoice()
        return {'type': 'ir.actions.report','report_name': 'ext_agro_rep_inventario.rentabilidad','report_type':"qweb-pdf"}