# -*- coding: utf-8 -*-
{
    'name': "ati_api_xswift",

    'summary': """
        Module Integration with XSwift""",

    'description': """
        Long description of module's purpose
    """,

    'author': "PT. Akselerasi Teknologi Investama",
    'website': "https://akselerasiteknologi.id/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','generic_request','sale','sale_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/config.xml',
        'views/views.xml',
        'wizard/message_api.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
