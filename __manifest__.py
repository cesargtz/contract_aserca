# -*- coding: utf-8 -*-
{
    'name': "contract_aserca",

    'summary': """
        Tablas Ori""",
    'author': "Yecora",
    'website': "yecora.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','truck_reception',],

    # always loaded
    'data': [
        'security/contract_access_rules.xml',
        'security/ir.model.access.csv',
        'views/related_contracts.xml',
    ],

}
