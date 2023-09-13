from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    global_discount_per_so_line = fields.Boolean("Global Discounts",
                                                 config_parameter="pos_sale_report.global_discount_per_so_line",
                                                 implied_group='products.global_discount_per_so_line')
    global_discount_value = fields.Float(string='Global Discount (%)',
                                         config_parameter="pos_sale_report.global_discount_value", default=0.0)
