'''
Created on Nov 12, 2020

@author: Zuhair Hammadi
'''
from odoo import models, _, fields, api
from odoo.exceptions import UserError

class AccountBankStatement(models.Model):
    _name = "account.bank.statement"
    _inherit = ["account.bank.statement", 'mail.thread', 'mail.activity.mixin']
    
    state = fields.Selection(string='Status', required=True, readonly=True, copy=False, tracking=True, selection=[
            ('open', 'New'),
            ('confirm', 'Validated'),
        ], default='open')
    
    line_count = fields.Integer(compute = '_calc_line_count')
    
    is_reconciled = fields.Boolean(
        string='Is Reconciled',
        compute='_compute_is_reconciled', store=True,
    )    
    
    journal_type = fields.Selection(related='journal_id.type', default = lambda self: self._context.get('journal_type'), inverse = '_inverse_journal_type')    
    
    def _inverse_journal_type(self):
        pass
        
    @api.depends('line_ids.is_reconciled')
    def _compute_is_reconciled(self):
        for record in self:
            record.is_reconciled = record.line_ids and all(record.mapped('line_ids.is_reconciled'))
    
    @api.depends('line_ids.journal_id')
    def _compute_journal_id(self):
        for statement in self:
            statement.journal_id = statement.line_ids.journal_id or statement.journal_id
            
            
    def button_validate(self):
        self.ensure_one()
        if self.state !='open' and not self.is_reconciled:
            raise UserError(_('Cannot validate bank statement'))
        
        self.state = 'confirm'    
        
        
    def button_reopen(self):
        self.state = 'open'
    
    @api.depends('line_ids')
    def _calc_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)
        
    def action_view_lines(self):
        ref = lambda name : self.env.ref(name).id
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Transactions'),
            'res_model' : 'account.bank.statement.line',
            'view_mode' : 'tree,form',
            'views' : [(ref('oi_bank_reconciliation.view_bank_statement_line_tree_reconciliation'), 'tree'), 
                       (ref('oi_bank_reconciliation.view_bank_statement_line_form_reconciliation'), 'form')
                       ],
            'domain' : [('statement_id','=', self.id)],
            'context' : {
                'default_statement_id' : self.id,
                'default_journal_id' : self.journal_id.id
                }
            }
                
    def action_transaction_generate(self):
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Generate Transactions'),
            'res_model' : 'account.bank.statement.generate',
            'view_mode' : 'form',
            'target' : 'new',
            'context' : {
                'default_statement_id' : self.id,                
                }   
            }
        
    def action_reconcile(self, line_id = None):
        line_ids = self.line_ids
        
        if line_id is not None:
            index = line_ids.ids.index(line_id.id)
            line_ids = line_ids[index + 1:]
        
        for line in line_ids:                            
            if not line.is_reconciled:
                try:
                    line.action_reconcile()
                except UserError:
                    return line.with_context(reconcile_all_line = True).button_reconciliation()
                
    def auto_balance_end(self):
        self.balance_end_real = self.balance_end