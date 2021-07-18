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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    condicion_producto = fields.Selection(selection=[('n', 'N/A'),('a', 'Otimo para la venta'),('b', 'Dañado y Vendible'),('c', 'Desechable')])