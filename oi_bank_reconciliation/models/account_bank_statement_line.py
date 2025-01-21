'''
Created on Nov 11, 2020

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

class AccountBankStatementLine(models.Model):
    _name = "account.bank.statement.line"
    _inherit = ['account.bank.statement.line', 'mail.thread', 'mail.activity.mixin']

    _rec_name = 'payment_ref'
    
    matched_payment_ids = fields.Many2many('account.payment', relation='bank_statement_line_matched_payment_rel', copy = False)
    matched_move_line_ids = fields.Many2many('account.move.line', relation='bank_statement_line_matched_move_line', copy = False)
    matched_manual_ids = fields.One2many('account.bank.statement.manual', 'statement_line_id')
    matched_balance = fields.Monetary(compute = "_calc_matched_balance", string='Open Balance')
    matched_balance_absolute = fields.Monetary(compute = "_calc_matched_balance", string='Open Balance (Absolute)')
    
    reconcile_state = fields.Selection([('Reconciled','Reconciled'),('Unreconciled','Unreconciled')], compute = '_calc_reconcile_state', string="Reconcile Status")
    
    is_reconciled = fields.Boolean(tracking = True, copy = False)
    amount_residual = fields.Float(tracking = True)
    amount = fields.Monetary(tracking = True)
    
    statement_state = fields.Selection(related='statement_id.state', string="Statement Status")
    
    edit_enabled = fields.Boolean(compute = '_calc_edit_enabled')

    reconciliation_range = fields.Float(related='journal_id.reconciliation_range')    
    
    @api.returns('self', lambda value:value.id)
    def copy(self, default=None):
        record = super(AccountBankStatementLine, self).copy(default = default)
        record.action_undo_reconciliation()
        return record
    
    @api.constrains('statement_id')
    @api.ondelete(at_uninstall=False)
    def _check_statement(self):
        for record in self:
            if record.statement_id.state =='confirm':
                raise ValidationError(_("Statement is validated"))
    
    @api.depends('is_reconciled','statement_state')
    def _calc_edit_enabled(self):
        for record in self:
            record.edit_enabled = not record.is_reconciled and record.statement_state !='confirm'
    
    @api.onchange('matched_manual_ids')
    def _onchange_matched_manual_ids(self, force_update = False):
        in_draft_mode = self != self._origin
        
        def need_update():
            amount = 0
            for line in self.matched_manual_ids:
                if line.auto_tax_line:
                    amount -= line.balance
                    continue
                if line.tax_ids:
                    balance_taxes_res = line.tax_ids._origin.compute_all(
                        line.balance,
                        currency=line.currency_id,
                        quantity=1,
                        product=line.product_id,
                        partner=line.partner_id,
                        is_refund=False,
                        handle_price_include=True,
                    )
                    for tax_res in balance_taxes_res.get("taxes"):
                        amount += tax_res['amount']
            return amount 
        
        if not force_update and not need_update():
            return
        
        to_remove = self.env['account.bank.statement.manual']        
        if self.matched_manual_ids:
            for line in list(self.matched_manual_ids):
                if line.auto_tax_line:
                    to_remove += line
                    continue
                if line.tax_ids:
                    balance_taxes_res = line.tax_ids._origin.compute_all(
                        line.balance,
                        currency=line.currency_id,
                        quantity=1,
                        product=line.product_id,
                        partner=line.partner_id,
                        is_refund=False,
                        handle_price_include=False,
                    )
                    
                    for tax_res in balance_taxes_res.get("taxes"):
                        create_method = in_draft_mode and line.new or line.create
                        create_method({
                            'statement_line_id' : self.id,
                            'account_id' : tax_res['account_id'],
                            'name' : tax_res['name'],
                            'balance' : tax_res['amount'],
                            'tax_repartition_line_id' : tax_res['tax_repartition_line_id'],
                            'tax_tag_ids' : tax_res['tag_ids'],
                            'auto_tax_line' : True,
                            'sequence' : line.sequence,
                            'tax_line_id' : line.id
                            })
                    
            if in_draft_mode:
                self.matched_manual_ids -=to_remove
            else:
                to_remove.unlink()
    
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        for vals in vals_list:
            if 'statement_id' not in vals and self._context.get('default_statement_id'):
                vals['statement_id'] = self._context.get('default_statement_id')
                
        return super(AccountBankStatementLine, self).create(vals_list)
    
    @api.depends('is_reconciled')
    def _calc_reconcile_state(self):
        for record in self:
            record.reconcile_state = record.is_reconciled and 'Reconciled' or 'Unreconciled'
    
    def button_reconciliation(self):
        ref = lambda name : self.env.ref(name).id
        context = dict(self._context)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Reconciliation'),
            'target' : 'new',
            'res_model' : 'account.bank.statement.line',
            'res_id' : self.id,
            'view_mode' : 'form',
            'views' : [(ref('oi_bank_reconciliation.view_bank_statement_line_form_reconciliation_popup'), 'form')], 
            'context' : context           
            }
    
    def _prepare_reconciliation(self, lines_vals_list, allow_partial=False):
        
        reconciliation_overview, open_balance_vals = super(AccountBankStatementLine, self)._prepare_reconciliation(lines_vals_list, allow_partial = allow_partial)
        
        
        for item in reconciliation_overview:
            payment_vals = item.get("payment_vals")
            if payment_vals:
                payment_vals['statement_line_ids'] = [(6,0, self.ids)]
                    
        return reconciliation_overview, open_balance_vals
            
    
    def action_reconcile_next(self):
        return self.statement_id.action_reconcile(line_id = self)        
    
    
    def action_reconcile(self): 
        self.ensure_one()
        
        if self.matched_balance != 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("The Reconciltion Amount Should Be Zero."),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        
        self._onchange_matched_manual_ids(force_update = True)
        
        liquidity_lines, suspense_lines, other_lines = self._seek_for_lines() # @UnusedVariable
        reconcile_lines = self._get_reconcile_lines()
        
        line_ids_vals = []
        for line in suspense_lines:
            line_ids_vals.append(Command.delete(line.id))        
                
        for line in reconcile_lines:            
            line_ids_vals.append(Command.create({
                'account_id' : line.account_id.id,
                'partner_id' : line.partner_id.id,
                'name' : self.payment_ref,
                'debit' : abs(line.amount_residual) if line.amount_residual <0 else 0,
                'credit' : abs(line.amount_residual) if line.amount_residual >0 else 0,
                'currency_id' : line.currency_id.id,
                'amount_currency' : -line.amount_residual_currency
                }))
            
        for line in self.matched_manual_ids:
            line_ids_vals.append(Command.create({
                'account_id' : line.account_id.id,
                'product_id': line.product_id.id,
                'partner_id' : line.partner_id.id,
                'name' : line.name,
                'debit' : abs(line.balance) if line.balance <0 else 0,
                'credit' : abs(line.balance) if line.balance >0 else 0,
                'currency_id' : line.currency_id.id,
                'amount_currency' : -line.balance,
                'tax_ids' : [Command.set(line.tax_ids.ids)],
                'tax_repartition_line_id' : line.tax_repartition_line_id.id
                }))     
                               
        if not self.matched_payment_ids.ids and not self.matched_move_line_ids.ids and not self.matched_manual_ids.ids:
            raise ValidationError(_("Please fill out one of Payment Matching or Customer/Vendor Matching or Manual Operations"))

        self.move_id.button_draft()
        self.move_id.with_context(force_delete = True).write({'line_ids' : line_ids_vals})
        self.move_id._post(False)
        #self.move_id.line_ids.analytic_line_ids.unlink()
        #self.move_id.line_ids._create_analytic_lines()
        
        liquidity_lines, suspense_lines, other_lines = self._seek_for_lines()  # @UnusedVariable
        
        for account_id, lines in (reconcile_lines + other_lines)._groupby('account_id'): # @UnusedVariable
            if account_id.reconcile:
                lines.reconcile()
        
        if self._context.get("reconcile_all_line"):
            return self.statement_id.action_reconcile(line_id = self)
    
                
    def _get_reconcile_lines(self):
        lines = self.env['account.move.line']
        
        for payment in self.matched_payment_ids:
            lines += payment.move_id.line_ids.filtered(lambda line: not line.reconciled and line.account_id.account_type not in ('asset_receivable', 'liability_payable') and line.account_id.reconcile)

        lines += self.matched_move_line_ids            
            
        return lines
            
                            
    @api.depends('matched_payment_ids','matched_move_line_ids','matched_manual_ids', 'is_reconciled')
    def _calc_matched_balance(self):
        for record in self:
            if not record.id:
                record.matched_balance = 0
                record.matched_balance_absolute = 0
                continue
            try:
                if record.is_reconciled:
                    record.matched_balance = record.amount_residual
                else:
                    record.matched_balance = record.amount_residual + sum(record._get_reconcile_lines().mapped('amount_residual')) + sum(record.mapped('matched_manual_ids.balance'))
            except UserError:
                record.matched_balance = 0
            record.matched_balance_absolute = abs(record.matched_balance)
                
            