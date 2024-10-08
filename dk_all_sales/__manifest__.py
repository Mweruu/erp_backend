{
    "name": "All Sales Reports",
    "version": "1.0",
    "category": "Productivity",
    "depends": ['purchase', 'sale_management'],
    "description": "Reports for goods sold on a specific date",
    "data": [
        "security/ir.model.access.csv",
        "views/sales.xml",
        "reports/sales_report.xml",
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
