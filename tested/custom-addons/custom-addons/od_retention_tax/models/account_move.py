from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    retention_tax = fields.Boolean('Retention Tax')
