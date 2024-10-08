{
    'name': 'Phone Payments',
    'version': '16.0.01',
    'description': 'Track daily transactions',
    'author': 'Younis',
    'depends': ['base', 'mail'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/phone_payment.xml',
        'views/phone_payment_report.xml',
        'reports/phone_payment.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',

}
