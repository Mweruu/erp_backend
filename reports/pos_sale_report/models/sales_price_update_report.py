from odoo import models, fields, api


class PriceDifference(models.Model):
    _name = "sales.price.difference"
    _description = "Sales price update report"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    datetime = fields.Datetime('Time')
    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    product_id = fields.Many2one("product.product")
    old_price = fields.Float('Old Price', digits='Product Price', required=True)
    user_id = fields.Many2one('res.users', required=True, default=_default_user)
    list_price = fields.Float('Sales Price', digits='Product Price', required=True)
