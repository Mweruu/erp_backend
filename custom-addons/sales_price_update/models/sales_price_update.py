from datetime import datetime, time
from odoo import models, fields, api


class PriceDifference(models.Model):
    _name = "sales.price.differences"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    product_id = fields.Many2one("product.product")

    old_price = fields.Float('Old Price', default=1.0, digits='Product Price')
    user_id = fields.Many2one('res.users', required=True, default=_default_user)
    list_price = fields.Float('Sales Price', default=1.0, digits='Product Price')

    def action_print_sales_price_difference_report(self):

        data = []
        domain = []
        if self.date_from:
            domain += [('create_date', '>=', self.date_from)]
        if self.date_to:
            domain += [('create_date', '<=', self.date_to)]

        sales_price_differences = self.env['sales.price.differences'].search([('date_from', '>=', self.date_from),
                                                                  ('date_to', '<=', self.date_to),
                                                                  ])

        for sales_price_difference in sales_price_differences:
            product_name = sales_price_difference['product_id']
            user_name = sales_price_difference['user_id']

            data.append({
                "Date from": sales_price_difference['date_from'],
                "Date to": sales_price_difference['date_to'],
                "Old Price": sales_price_difference['old_price'],
                "Sales Price": sales_price_difference['list_price'],
                "User_id": user_name.name,
                'Product_id': product_name.name,
            })

        data = {
            'records': data,
            'self': self.read()[0]
        }

        return self.env.ref('sales_price_update.sales_price_difference_report').report_action(self, data=data)
