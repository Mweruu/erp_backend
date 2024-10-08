from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_set_product_name = fields.Boolean(related='company_id.is_set_product_name', readonly=False, store=True)
    is_product_name = fields.Text(related='company_id.is_product_name', string='Custom Product Name for invoice',
                                  compute='_compute_custom_product_name', readonly=False, store=True)

    @api.depends('is_set_product_name', 'company_id')
    def _compute_custom_product_name(self):
        for res_config in self:
            if res_config.is_set_product_name:
                res_config.is_product_name = res_config.company_id.is_product_name
            else:
                res_config.is_product_name = False
