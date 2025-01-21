'''
Created on Nov 15, 2020

@author: Zuhair Hammadi
'''
from odoo import fields, models
import odoo

class AccountJournal(models.Model):
    _inherit = "account.journal"

    reconciliation_range = fields.Float()
    
    def get_journal_dashboard_datas(self):
        res = super(AccountJournal, self).get_journal_dashboard_datas()
        isEnterprise = odoo.service.common.exp_version()['server_version_info'][-1] == 'e'
        res.update({
            'show_reconcile_items' : res['number_to_reconcile'] and not isEnterprise
            })
        return res

    def action_statement_reconcile(self):
        ref = lambda name : self.env.ref(name).id
        return {
            'type' : 'ir.actions.act_window',
            'name' : self.name,
            'res_model' : 'account.bank.statement.line',
            'view_mode' : 'tree,form',
            'views' : [(ref('oi_bank_reconciliation.view_bank_statement_line_tree_reconciliation'), 'tree'), 
                       (ref('oi_bank_reconciliation.view_bank_statement_line_form_reconciliation'), 'form')
                       ],
            'domain' : [('journal_id','=', self.id), ('is_reconciled','=', False)],          
            'context' : {
                'from_dashboard' : True
                }
            }        