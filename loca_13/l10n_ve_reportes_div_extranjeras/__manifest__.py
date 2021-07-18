# -*- coding: utf-8 -*-
{
    'name': "Edos Financieros de Moneda Local a Mon Extranjera",

    'summary': """Edos Financieros de Moneda Local a Mon Extranjera""",

    'description': """
       Edos Financieros de Moneda Local a Mon Extranjera.
    """,
    'version': '13.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'category': 'Tools',
    'website': 'http://soluciones-tecno.com/',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'report/reporte_view.xml',
        'wizard/wizard.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
    'active':False,
    'auto_install': False,
}
