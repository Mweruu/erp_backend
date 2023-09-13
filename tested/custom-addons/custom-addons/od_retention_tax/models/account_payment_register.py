from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    tax_id = fields.Many2one('account.tax', string='Tax Type')
    tax_amount = fields.Float('Tax Amount', compute="compute_tax_amount")
    tax_type = fields.Char('Tax categ', compute="get_tax_type")

    @api.depends('journal_id')
    def get_tax_type(self):
        if self.partner_type == 'customer':
            self.tax_type = 'sale'
        if self.partner_type == 'supplier':
            self.tax_type = 'purchase'
        if not self.partner_type:
            self.tax_type = 'none'

    @api.depends('tax_id', 'amount')
    def compute_tax_amount(self):
        self.tax_amount = 0
        if self.tax_id:
            self.tax_amount = self.tax_id.compute_all(self.amount)['taxes'][0].get('amount')

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        payment_vals['tax_id'] = self.tax_id.id
        return payment_vals

    def action_create_payments(self):
        if self.tax_id and self.payment_difference != 0 and self.payment_difference_handling == 'reconcile':
            raise UserError('You can not create payment. Keep the invoice open with partial payment.')
        return super(AccountPaymentRegister, self).action_create_payments()
