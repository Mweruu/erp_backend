# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import fields, models, api


class purchase_history(models.Model):
    _name = 'purchase.history'
    _description = 'purchase.history'
    _rec_name = 'po_order'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Supplier", domain=[('supplier', '=', True)])
    order_date = fields.Datetime(string="Date")
    qty = fields.Float(string="Quantity")
    product_id = fields.Many2one('product.template', string='product')
    po_order = fields.Many2one('purchase.order', string='PO Number')
    remark = fields.Char(string='Remark')
    price = fields.Float(string='Price')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line')
    computed_cost = fields.Float(string='Computed Cost', compute='_compute_average_cost')

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
    def _compute_average_cost(self):
        sorted_self = sorted(self, key=lambda x: x.order_date, reverse=True)
        qty_available = self.product_id.qty_available
        sum_qty = 0
        total = 0
        if qty_available <= 0:
            self.computed_cost = sorted_self[0].price if sorted_self else 0
            return

        for record in sorted_self:
            if sum_qty + record.qty <= qty_available:
                sum_qty += record.qty
                total += record.price * record.qty
            else:
                remaining_qty = qty_available - sum_qty
                total += remaining_qty * record.price
                sum_qty += remaining_qty
                break
        self.computed_cost = total / qty_available
