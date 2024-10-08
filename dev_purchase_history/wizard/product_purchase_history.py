# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import fields, models


class purchase_product_history(models.TransientModel):
    _name = "purchase.product.history"
    _description = 'purchase product history'

    purchase_product_line = fields.One2many('purchase.history.line', 'product_his_id', string="PO Line")


class purchase_product_history_line(models.TransientModel):
    _name = "purchase.history.line"
    _description = 'purchase history line'

    product_his_id = fields.Many2one('purchase.product.history')
    supplier_id = fields.Many2one('res.partner', string="Supplier")
    po_number = fields.Char('PO Number')
    order_date = fields.Datetime(string="Date")
    qty = fields.Float(string="Quantity")
    product_id = fields.Many2one('product.template', string='Product')
    price = fields.Float(string='Price')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
