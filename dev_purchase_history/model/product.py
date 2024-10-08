# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def view_purchase_order_lines(self):
        if 'product_tmpl_id' in self._fields:
            purchase_line_ids = self.env['purchase.order.line'].search([('product_id', '=', self.id)])
        else:
            purchase_line_ids = self.env['purchase.order.line'].search([('product_id.product_tmpl_id', '=', self.id)])
        tree_id = self.env.ref('dev_purchase_history.tree_purchase_line_dev_purchase_history').id
        if purchase_line_ids:
            return {'name': 'Purchase Order Lines',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'res_model': 'purchase.order.line',
                    'views': [(tree_id, 'tree')],
                    'target': 'current',
                    'domain': [('id', 'in', purchase_line_ids.ids)]
                    }
        else:
            raise ValidationError(_('''Purchase Order Lines not found for '%s' ''') % (self.name))

    purchase_history_ids = fields.One2many('purchase.history', 'product_id', string='History', copy=False)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def view_purchase_order_lines(self):
        if 'product_tmpl_id' in self._fields:
            purchase_line_ids = self.env['purchase.order.line'].search([('product_id', '=', self.id)])
        else:
            purchase_line_ids = self.env['purchase.order.line'].search([('product_id.product_tmpl_id', '=', self.id)])
        tree_id = self.env.ref('dev_purchase_history.tree_purchase_line_dev_purchase_history').id
        if purchase_line_ids:
            return {'name': 'Purchase Order Lines',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'res_model': 'purchase.order.line',
                    'views': [(tree_id, 'tree')],
                    'target': 'current',
                    'domain': [('id', 'in', purchase_line_ids.ids)]
                    }
        else:
            raise ValidationError(_('''Purchase Order Lines not found for '%s' ''') % (self.name))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
