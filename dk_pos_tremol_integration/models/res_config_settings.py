from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_is_send_to_TIMS = fields.Boolean(related='pos_config_id.is_send_to_TIMS', readonly=False, store=True)
    pos_is_set_product_name = fields.Boolean(related='pos_config_id.is_set_product_name', readonly=False, store=True)
    pos_is_product_name = fields.Text(string='Custom Product Name', compute='_compute_pos_is_product_name',
                                      readonly=False, store=True)
    l10n_pos_ke_cu_proxy_address = fields.Char(related='pos_config_id.l10n_pos_ke_cu_proxy_address', readonly=False)

    @api.depends('pos_is_set_product_name', 'pos_config_id')
    def _compute_pos_is_product_name(self):
        for res_config in self:
            if res_config.pos_is_set_product_name:
                res_config.pos_is_product_name = res_config.pos_config_id.is_product_name
            else:
                res_config.pos_is_product_name = False
