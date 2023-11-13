from odoo import models, fields, _, api
from odoo.tools import float_compare
from odoo.exceptions import ValidationError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    def is_amount_to_approve(self):
        self.ensure_one()
        currency = self.company_id.currency_id
        limit_amount = self.company_id.so_double_validation_amount
        limit_amount = currency.compute(limit_amount, self.currency_id)
        return float_compare(limit_amount, self.amount_total, precision_rounding=self.currency_id.rounding) <= 0

    def is_to_approve(self):
        self.ensure_one()
        return (self.company_id.so_double_validation == 'two_step' and self.is_amount_to_approve() and
                not self.user_has_groups('od_sale_order_workflow.sale_order_approval'))

    def action_confirm(self):
        if self.is_to_approve() and self.state in ('draft', 'sent'):
            self.state = 'to_approve'
            return True
        res = super(SaleOrder, self).action_confirm()
        return res
