'''
Created on Nov 15, 2020

@author: Zuhair Hammadi
'''
from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    statement_line_ids = fields.Many2many(comodel_name='account.bank.statement.line', 
                                          relation='account_payment_account_bank_statement_line_rel',
                                          string = 'Auto-generated for statements') 
    
    match_statement_line_ids = fields.Many2many('account.bank.statement.line', relation='bank_statement_line_matched_payment_rel')