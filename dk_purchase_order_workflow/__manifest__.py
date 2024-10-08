{
    'name': "Purchase Order Automation",
    'version': '16.0.1.0',
    'category': 'Purchases',
    'author': 'Younis',
    'depends': ['purchase', 'purchase_stock', "bus"],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'data/auto_cron_ywt_purchase_order_automation.xml',
        'data/ywt_purchase_order_automation_history_sequence.xml',
        'views/rejection_wizard.xml',
        'views/purchase_view.xml',
        'views/purchase_report_template.xml',
        'views/approval_info.xml',
        'views/purchase_approval_config.xml',
        'views/purchase_approval_line.xml',
        'views/res_config_setting.xml',
        'views/ywt_purchase_order_automation_views.xml',
        'views/ywt_purchase_order_automation_history_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {

        'web.assets_backend': [
            'dk_purchase_order_workflow/static/src/js/bus_notification.js',
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',

}
