# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo 16 Reporting ',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': '',
    'description': 'Odoo 16  Statement Reports Module(journal items report)'
                   'All Sales Report Module'
                   'Withholding Tax Report Module'
                   'Return Merchandise Authorization Module'
                   'Internal Consumption Module'
                   'Product Stock Card Report'
                   'Inventory Ledger Report'
                   'Import Stock Inventory'
                   'Internal Stock Transfer',
    'sequence': '1',
    'license': 'LGPL-3',
    'depends': [
        'dk_journal_items_report',
        'dk_all_sales',
        'dk_withholding_tax_report',
        'rma_ept',
        'internal_consumption',
        'dev_stock_card_report',
        'setu_inventory_ledger_report',
        'import_stock_inventory_app',
        'internal_stock_transfer_app',
    ],
    'demo': [],
    'data': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
