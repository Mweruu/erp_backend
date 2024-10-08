# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import models, api, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def unlink(self):
        history_ids = self.env['purchase.history'].search([('po_order', '=', self.id)])
        if history_ids:
            for line in history_ids:
                line.unlink()
        super(PurchaseOrder, self).unlink()

    def create_purchase_line_history(self):
        if self.order_line:
            history_pool = self.env['purchase.history']
            for line in self.order_line:
                if line.history_created:
                    history_line_id = history_pool.search([('purchase_line_id', '=', line.id)], limit=1)
                    if history_line_id:
                        history_line_id.unlink()
                        values = {'partner_id': line.order_id.partner_id.id or False,
                                  'order_date': line.order_id.date_order or '',
                                  'qty': line.product_qty or 0.0,
                                  'product_id': line.product_id.product_tmpl_id.id or False,
                                  'po_order': line.order_id.id or False,
                                  'price': line.price_unit or 0.00,
                                  'purchase_line_id': line.id
                                  }
                        history_pool.create(values)
                else:
                    values = {'partner_id': line.order_id.partner_id.id or False,
                              'order_date': line.order_id.date_order or '',
                              'qty': line.product_qty or 0.0,
                              'product_id': line.product_id.product_tmpl_id.id or False,
                              'po_order': line.order_id.id or False,
                              'price': line.price_unit or 0.00,
                              'purchase_line_id': line.id
                              }
                    history_pool.create(values)
                    line.history_created = True

    def button_approve(self, force=False):
        super(PurchaseOrder, self).button_approve(force=False)
        self.create_purchase_line_history()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def view_purchase_history(self):
        po_serach = self.env['purchase.order.line'].search([('product_id', '=', self.product_id.id)])
        res = []
        if po_serach:
            for po_line in po_serach:
                res.append((0, 0,
                            {'supplier_id': po_line.order_id.partner_id and po_line.order_id.partner_id.id,
                             'po_number': po_line.order_id.name,
                             'product_id': po_line.product_id and po_line.product_id.product_tmpl_id and po_line.product_id.product_tmpl_id.id or False,
                             'order_date': po_line.date_order,
                             'price': po_line.price_unit,
                             'qty': po_line.product_qty
                             }))
        res_sorted = sorted(res, key=lambda x: x[2]['order_date'], reverse=True)
        po_history_id = self.env['purchase.product.history'].create({'purchase_product_line': res_sorted})
        return {'view_mode': 'form',
                'res_id': po_history_id.id,
                'res_model': 'purchase.product.history',
                'view_type': 'form',
                'name': 'Product History',
                'type': 'ir.actions.act_window',
                'target': 'new'
                }

    history_created = fields.Boolean(string='History Created', copy=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
