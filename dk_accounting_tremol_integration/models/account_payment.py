from odoo import models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Payments"
    _order = "date desc, name desc"
    _check_company_auto = True

    def action_draft(self):
        ''' posted -> draft '''
        if self.state == 'posted' and not self.user_has_groups("account.group_account_manager"):
            raise ValidationError("Cannot Reset a Posted Entry")
        else:
            super(AccountPayment, self).action_draft()
