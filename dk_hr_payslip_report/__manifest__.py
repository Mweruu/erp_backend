{
    'name': 'Payroll Reports',
    'version': '16.0.1',
    'category': 'Payroll',
    'license': "AGPL-3",
    'summary': "Payroll reports",
    'author': "",
    'depends': [
        'om_hr_payroll'
    ],
    'data': [
        "security/ir.model.access.csv",
        'views/hr_payslip_views.xml',
        'reports/hr_payslip_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
