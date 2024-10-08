from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    global_discount_per_so_line = fields.Boolean("Global Discount",
                                                 config_parameter="dk_pos_sale_report.global_discount_per_so_line",
                                                 implied_group='products.global_discount_per_so_line')
    global_discount_value = fields.Float(string='Global Discount (%)',
                                         config_parameter="dk_pos_sale_report.global_discount_value", default=0.0)
    sale_tax_id = fields.Many2one('account.tax', string="Default Sale Tax", related='company_id.account_sale_tax_id',
                                  readonly=False, config_parameter='dk_pos_sale_report.sale_tax_id')
