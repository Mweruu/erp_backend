# -*- coding: utf-8 -*-pack
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_auto_purchase_order_automation = fields.Boolean(string="Set Purchase Order Automation", default=False)
    ywt_purchase_order_automation_id = fields.Many2one('ywt.purchase.order.automation', string='Purchase Order Automation')
    
