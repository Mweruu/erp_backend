{
    'name': 'POS Return Order',
    'version': '16.0.1.0.0',
    'summary': """Option to select the customised Receipts for each POS""",
    'description': "Option to select the customised Receipts for each POS",
    'category': 'Point of Sale',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'point_of_sale'],
    'data': [
        "views/res_config_settings_views.xml",
    ],
    'assets': {
        'point_of_sale.assets': [
            'dk_pos_return_orders/static/src/js/**/*.js',
            'dk_pos_return_orders/static/src/xml/**/*.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
