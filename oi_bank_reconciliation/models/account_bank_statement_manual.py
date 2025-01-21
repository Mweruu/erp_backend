'''
Created on Nov 12, 2020

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class AccountBankStatementLine(models.Model):
    _name = "account.bank.statement.manual"
    _inherit = ['analytic.mixin']
    _description = "Bank Statement Line Manual Operation"
    _order = 'sequence,id'

    sequence = fields.Integer()
    statement_line_id = fields.Many2one('account.bank.statement.line', required = True, ondelete ='cascade')
    currency_id = fields.Many2one(related='statement_line_id.currency_id')
    company_id = fields.Many2one(related='statement_line_id.company_id')    
    account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id),('is_off_balance', '=', False)]", check_company=True)
    name = fields.Char(string='Label')
    balance = fields.Monetary('Amount')
    partner_id = fields.Many2one('res.partner')
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount", check_company=True)
    
    product_id = fields.Many2one('product.product', string='Product')
    
    tax_tag_ids = fields.Many2many(string="Tags", comodel_name='account.account.tag', ondelete='restrict',
        help="Tags assigned to this line by the tax creating it, if any. It determines its impact on financial reports.")
    
    tax_repartition_line_id = fields.Many2one(comodel_name='account.tax.repartition.line',
        string="Originator Tax Distribution Line", ondelete='restrict', readonly=True,
        check_company=True,
        help="Tax distribution line that caused the creation of this move line, if any")    
    auto_tax_line = fields.Boolean()
    
    tax_line_id = fields.Many2one("account.bank.statement.manual", readonly = True, ondelete = 'cascade')
    
    @api.depends('product_id', 'account_id')
    def _compute_analytic_distribution(self):
        for record in self:
            distribution = self.env['account.analytic.distribution.model']._get_distribution({
                'product_id': record.product_id.id,
                'product_categ_id': record.product_id.categ_id.id,
                'account_prefix': record.account_id.code,
                'company_id': record.company_id.id,
            })
            record.analytic_distribution = distribution or record.analytic_distribution
    
                                                                                            
    @api.onchange('balance')
    def _onchange_statement_line_id(self):
        if not self.balance:
            self.balance = self.statement_line_id.matched_balance            

    @api.onchange('account_id')
    def _onchange_account_id(self):
        if self.account_id and not self.name:
            self.name = self.account_id.name
            