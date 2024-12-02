{
    "name": "POS KRA Integration",
    "version": "1.0",
    "category": "Productivity",
    "depends": ['l10n_ke_edi_tremol', 'point_of_sale'],
    "description": "TREMOL",
    "data": [
        "security/ir.model.access.csv",
        'views/res_config_settings_views.xml',
        'views/pos_order_tremol_integration.xml',
        'views/tax_report_views.xml',
        'views/summary_tax_report_views.xml',
        'views/tremol_data_views.xml',
        'reports/summary_tax_report.xml',
        'reports/tax_report.xml',
        'reports/tremol_data.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            "dk_pos_tremol_integration/static/src/js/PaymentScreen.js",
            "dk_pos_tremol_integration/static/src/js/model.js",
            "dk_pos_tremol_integration/static/src/js/send_invoice.js",
        ],
        'web.assets_qweb': [],
    },
    'license': 'LGPL-3',
}
