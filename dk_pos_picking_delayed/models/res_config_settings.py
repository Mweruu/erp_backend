from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_picking_creation_delayed = fields.Boolean(related='pos_config_id.picking_creation_delayed', readonly=False,
                                                  store=True)
