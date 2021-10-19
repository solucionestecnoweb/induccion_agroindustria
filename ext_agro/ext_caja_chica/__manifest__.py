{
    'name': 'Caja Chica',
    'description': 'Caja Chica para registrar pagos con efectivo divisas',
    'version': '13.0.1.0.0',
    'author': 'Ing. Darrell Sojo',
    'depends': ['account', 'base','sale','sale_management'],
    'data': [
        'views/menu.xml',
        'views/menu_2.xml',
        'security/ir.model.access.csv',
        #'views/wizard_legal_ledger.xml',
        #'reports/legal_ledger_report.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
