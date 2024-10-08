from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DKPhonePayment(models.Model):
    _name = 'dk.phone.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Phone Payment'
    _order = 'id desc'

    def get_default_start_time(self):
        previous_payment = self.env['dk.phone.payment'].search([('state', '!=', 'cancel')], limit=1)
        return previous_payment.session_end_time

    def get_default_opening_balance(self):
        previous_payment = self.env['dk.phone.payment'].search([('state', '!=', 'cancel')], limit=1)
        return previous_payment.closing_balance

    name = fields.Char('Number', default='/')
    session_start_time = fields.Datetime('Session Start', default=get_default_start_time)
    session_end_time = fields.Datetime('Session End')
    last_transaction_id = fields.Char('Last transaction ID')
    last_transaction_amount = fields.Monetary('Last transaction amount')
    opening_balance = fields.Monetary('Opening Balance', default=get_default_opening_balance)
    closing_balance = fields.Monetary('Closing Balance')
    volume_amount = fields.Monetary('Volume amount', compute='compute_volume_amount')
    total_withdrawal = fields.Monetary('Total Withdrawals', compute='_compute_total_withdrawal')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('validate', 'Validated'), ('cancel', 'Cancelled')],
        default='draft', tracking=True)
    line_ids = fields.One2many('dk.phone.payment.line', 'phone_payment_id', string='Withdrawals')

    def unlink(self):
        for record in self:
            if record.state in ('confirm', 'validate'):
                raise UserError(_('You can not delete record in confirm or validate state!'))
        return super(DKPhonePayment, self).unlink()

    @api.depends('line_ids', 'closing_balance', 'opening_balance')
    def compute_volume_amount(self):
        for record in self:
            record.volume_amount = record.closing_balance + record.total_withdrawal - record.opening_balance

    @api.depends('line_ids')
    def _compute_total_withdrawal(self):
        for record in self:
            record.total_withdrawal = sum(record.line_ids.mapped('amount'))

    # @api.model
    # def create(self, vals):
    #     previous_payment = self.env['dk.phone.payment'].search([('state', '!=', 'cancel')], limit=1)
    #     vals['opening_balance'] = previous_payment.closing_balance
    #     # vals['session_start_time'] = previous_payment.session_end_time
    #     res = super(DKPhonePayment, self).create(vals)
    #     if res.name == '/':
    #         sequence_id = self.env.ref('dk_phone_payment.phone_payment_sequence').id
    #         if sequence_id:
    #             res.name = self.env['ir.sequence'].get_id(sequence_id)
    #         else:
    #             raise UserError(_('No Sequence found!'))
    #     return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            previous_payment = self.env['dk.phone.payment'].search([('state', '!=', 'cancel')], limit=1,
                                                                   order="id desc")
            if previous_payment:
                vals['opening_balance'] = previous_payment.closing_balance
                # Uncomment and adjust the following line if you need to set the session start time
                # vals['session_start_time'] = previous_payment.session_end_time
            else:
                vals['opening_balance'] = 0.0  # Or any default value you consider appropriate

            res = super(DKPhonePayment, self).create([vals])[0]
            if res.name == '/':
                sequence_id = self.env.ref('dk_phone_payment.phone_payment_sequence').id
                if sequence_id:
                    res.name = self.env['ir.sequence'].get_id(sequence_id)
                else:
                    raise UserError(_('No Sequence found!'))
        return res

    def action_confirm(self):
        for record in self:
            record.state = 'confirm'

    def action_validate(self):
        for record in self:
            record.state = 'validate'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'


class DKPhonePaymentLine(models.Model):
    _name = 'dk.phone.payment.line'
    _description = 'Phone Payment Line'

    phone_payment_id = fields.Many2one('dk.phone.payment', string='Phone Payment')
    date = fields.Datetime('DateTime', required=True)
    amount = fields.Monetary('Amount', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)
