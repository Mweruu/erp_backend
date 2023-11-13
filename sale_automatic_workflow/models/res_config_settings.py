from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_double_validation = fields.Selection(
        [
            ('one_step', 'Confirm sale orders in one step'),
            ('two_step', 'Get 2 levels of approvals to confirm a sale order')
        ],
        string="Levels of Approvals",
        default='one_step',
        help="Provide a double validation mechanism for purchases"
    )

    so_double_validation_amount = fields.Monetary(
        string='Double validation amount',
        default=5000,
        help="Minimum amount for which a double validation is required"
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        so_double_validation = self.env.user.company_id.so_double_validation
        so_double_validation_amount = self.env.user.company_id.so_double_validation_amount
        res.update(so_double_validation=so_double_validation)
        res.update(so_double_validation_amount=so_double_validation_amount)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.so_double_validation = self.so_double_validation
        self.env.user.company_id.so_double_validation_amount = self.so_double_validation_amount
