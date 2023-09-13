from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    retention_tax_id = fields.Many2one('account.tax', string="Default Retention Tax",
                                       related='company_id.account_retention_tax_id',
                                       readonly=False, config_parameter="od_retention_tax.retention_tax_id")


class ResCompany(models.Model):
    _inherit = "res.company"

    account_retention_tax_id = fields.Many2one('account.tax', string="Default Retention Tax")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # def _get_computed_taxes(self):
    #
    #     if self.move_id.is_sale_document(include_receipts=True):
    #         # Out invoice.
    #         if self.product_id.taxes_id:
    #             tax_ids = self.product_id.taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
    #         else:
    #             tax_ids = self.account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'sale')
    #         if not tax_ids and not self.exclude_from_invoice_tab:
    #             tax_ids = self.move_id.company_id.account_retention_tax_id
    #     else:
    #         # Miscellaneous operation.
    #         tax_ids = self.account_id.tax_ids
    #
    #     return super(AccountMoveLine, self)._get_computed_taxes()
