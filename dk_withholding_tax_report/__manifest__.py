{
    'name': 'Withholding Tax',
    'version': '16.0.1',
    'category': 'Accounting',
    'license': "AGPL-3",
    'summary': "Withholding Tax on Payments",
    'author': "Younis",
    'depends': [
        'sale',
        'purchase',
        'account',
        'payment',
    ],
    'data': [
        "security/ir.model.access.csv",
        'views/withholding.xml',
        'reports/withholding_tax_reports.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
