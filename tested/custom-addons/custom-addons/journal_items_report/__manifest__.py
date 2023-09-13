{
    'name': 'Statement Reports',
    'version': '15.0.1',
    'category': 'Journalling',
    'license': "AGPL-3",
    'summary': "Journal reports for all cash/bank journal items",
    'author': "",
    'depends': [
        'account',
    ],
    'data': [
        "security/ir.model.access.csv",
        'views/journals.xml',
        'reports/journals_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
