# -*- coding: utf-8 -*-


{
    "name": "Import Stock Inventory(Add/Update)",
    "author": "Edge Technologies",
    'version': '15.0.1.0',
    'live_test_url': "https://youtu.be/pCHq3VHv7ds",
    "images": ['static/description/main_screenshot.png'],
    'summary': "Import stock import inventory import stocks import stock inventory adjustment import inventory adjustment import stock inventory import stock inventory adjustment from excel import stock inventory with lot stock inventory import import delivery.",
    'description': """This app provides a functionality to import inventory adjustment from many given options.
    
Import stock import inventory import import stocks import stock inventory adjustment import inventory adjustment
Stock inventory import import stock inventory adjustment from csv/excel file import stock inventory with lot/serial number from csv/excel file stock inventory adjustments import using csv import delivery orders incoming shipments and internal tranfer
Import stock inventory adjustment from csv/xlsx import stock inventory with serial/lot number import stock inventory by csv/xlsx import stock inventory by barcode
 Import delivery orders  import incoming shipments import internal transfer import picking
 Import multiple pickings import warehosue data import stock inventory from csv importing inventory
 Import inventory by product import stock with lot number import inventory with lot number import lot with stock import stock balance import stock data import odoo stock import data on odoo
Update import adjustment update lot stock update stock adjustment update inventory stock adjustment import lot with inventory adjustment
Import stock with lot number import stock with product details update stock with product.


    """,
    "license": "OPL-1",
    "depends": ['base', 'stock', 'sale_management', 'purchase', 'account'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/import_wizard.xml',
        'wizard/validation.xml',
    ],
    'installable': True,
    'auto_install': False,
    'price': 18,
    'currency': "EUR",
    'category': 'warehouse',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
