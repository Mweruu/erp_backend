# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo 16 POS Modules ',
    'version': '1.0.0',
    'category': 'Point of Sale',
    'summary': '',
    'description': 'Odoo 16 Install POS and Sales Reports Module Automated Action Rules Module Phone Payments Module',
    'sequence': '1',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'dk_pos_sale_report',
        'dk_phone_payment',
        'dk_custom_receipts_for_pos',
        'dk_pos_return_orders',
        'dk_pos_picking_delayed',
        'dk_pos_tremol_integration',
    ],
    'demo': [],
    'data': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
