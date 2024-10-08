# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Internal Consumption (Internal Usage)',
    'author': 'Altela Software',
    'version': '16.0.1.0.0',
    'summary': 'Allows you to consume your product for company internal use.',
    'license': 'OPL-1',
    'sequence': 1,
    'price': '55',
    'currency': 'USD',
    'category': 'Inventory',
    'website': 'https://www.altelasoftware.com',
    'depends': [
        'stock',
        'hr_expense',
    ],
    'images': [
        'static/description/banner.gif',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/internal_consumption.xml',
        'views/internal_expense_views.xml',
        'views/menu.xml',
        'views/sequences.xml',
        'reports/internal_expense_reports.xml',
        'reports/deliveryslip.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    # 'pre_init_hook': 'pre_init_check',
}
