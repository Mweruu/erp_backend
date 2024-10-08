# -*- coding: utf-8 -*-
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseApprovalConfig(models.Model):
    _name = 'sh.purchase.approval.config'
    _description = 'Purchase Approval Configuration'

    name = fields.Char()
    min_amount = fields.Float(string="Minimum Amount", required=True)
    company_ids = fields.Many2many(
        'res.company', string="Allowed Companies", default=lambda self: self.env.company)
    is_boolean = fields.Boolean(string="User Always in CC")
    purchase_approval_line = fields.One2many(
        'sh.purchase.approval.line', 'purchase_approval_config_id')

    @api.constrains('purchase_approval_line')
    def approval_line_level(self):
        if self.purchase_approval_line:
            levels = self.purchase_approval_line.mapped('level')
            if len(levels) != len(set(levels)):
                raise ValidationError('Levels must be different!!!')
