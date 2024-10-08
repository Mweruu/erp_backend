# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Product Purchase History, Purchase Price History, Purchase histrory',
    'version': '1.0',
    'sequence': 1,
    'category': 'Purchases',
    'description':
        """
This Module add below functionality into odoo

        1.Shows history of the purchase orders into product screen\n

Product Purchase History 
Odoo Product Purchase History 
Manage product purchase History 
Odoo manage product purchase History
Odoo application allows you to track purchase history of products and also show quick purchase history of product on purchase order line.
Track Purchase History of Products
Odoo Track Purchase History of Products
Product Purchase History displayed in separate tab in product screen
Odoo Product Purchase History displayed in separate tab in product screen
You can also access Product Purchase History from Purchase Order Line via button
Odoo You can also access Product Purchase History from Purchase Order Line via button
Product Purchase History will be created when you confirm a Purchase Order
Odoo Product Purchase History will be deleted when you delete a Purchase Order
You can add remark into Purchase History of Product
Odoo You can add remark into Purchase History of Product


    """,
    'summary': 'Odoo apps will show product purchase history on product Screen | Purchase history | Product Purchase History | Purchase line Product History, product template purchase history, product purchase cost history',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_history.xml',
        'views/product_view.xml',
        'views/purchase_order_view.xml',
        'wizard/product_purchase_history.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,

    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd',
    'support': 'devintelle@gmail.com',
    'price': 8.0,
    'currency': 'EUR',
    "license": "AGPL-3",
    # 'live_test_url':'https://youtu.be/A5kEBboAh_k',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
