{
    'name': "Kenya Tremol Device EDI Integration Upgrade",
    'summary': """
            Kenya Tremol Device EDI Integration
        """,
    'description': """
       This module integrates with the Kenyan G03 Tremol control unit device to the KRA through TIMS.
    """,
    'category': 'Accounting/Localizations/EDI',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['l10n_ke', 'l10n_ke_edi_tremol'],
    'data': [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "views/account_move_view.xml",
        "views/res_config_settings_view.xml",
    ],

    'assets': {
    'web.assets_backend': [
        'dk_accounting_tremol_integration/static/src/js/send_invoice.js',
    ],
},
}
