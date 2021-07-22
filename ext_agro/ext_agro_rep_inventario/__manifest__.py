# -*- coding: utf-8 -*-
{
    'name': "Reportes Modificados de Inventario",

    'summary': """Reportes de Inventario""",

    'description': """
       Reportes Modificados de Inventario.
    """,
    'version': '13.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'category': 'Tools',
    'website': 'http://soluciones-tecno.com/',

    # any module necessary for this one to work correctly
    'depends': ['base','account','purchase','sale','stock','mrp','odoo_process_costing_manufacturing'],

    # always loaded
    'data': [
        'formatos/vale_entrega.xml',
        'formatos/wizard_resumen_semanal_produccion.xml',
        'formatos/wizard_rentabilidad_producto.xml',
        'formatos/stock_location_inherit_view.xml',
        'formatos/reporte_resumen_semanal_produccion.xml',
        'formatos/reporte_rentabilidad.xml',
        'formatos/product_template_inherit.xml',
        'formatos/mrp_routing_inherit.xml',
        'formatos/uom_uom_inherit.xml',
        'security/ir.model.access.csv',
        #'formatos/solicitud_ventas.xml',
        #'formatos/pedido_venta.xml',
        #'formatos/sale_order.xml',
        #'resumen_iva/reporte_view.xml',
        #'resumen_iva/wizard.xml',
        #'resumen_municipal/wizard.xml',
        #'resumen_municipal/reporte_view.xml',
        #'resumen_islr/wizard.xml',
        #'resumen_islr/reporte_view.xml',
    ],
    'application': True,
    'active':False,
    'auto_install': False,
}
