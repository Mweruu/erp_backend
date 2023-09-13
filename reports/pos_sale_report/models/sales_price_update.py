import base64
import csv
import io
from datetime import datetime

import pytz
from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PriceDifference(models.Model):
    _name = "sales.price.differences"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())
    user_id = fields.Many2one('res.users', required=True, default=_default_user)

    def get_sales_price_difference_report_data(self):
        data = []

        sales_price_differences = self.env['sales.price.difference'].search([('date_from', '>=', self.date_from),
                                                                             ('date_to', '<=', self.date_to),
                                                                             ])
        for sales_price_difference in sales_price_differences:
            product_name = sales_price_difference['product_id']
            user_name = sales_price_difference['user_id']
            old_price = sales_price_difference['old_price']
            list_price = sales_price_difference['list_price']
            diff = int(float(list_price)) - int(float(old_price))
            logger.debug(f"old price: {old_price}, list price:{list_price},Difference: {diff}")
            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = sales_price_difference['create_date'].astimezone(local_tz)
            if product_name:
                data.append({
                    "Date from": sales_price_difference['date_from'],
                    "Date to": sales_price_difference['date_to'],
                    "Old Price": sales_price_difference['old_price'],
                    "Sales Price": sales_price_difference['list_price'],
                    "User_id": user_name.name,
                    'Product_id': product_name.name,
                    'Price Difference': diff,
                    'Time': local_create_date.strftime('%d-%m-%Y, %H:%M:%S'),
                })
        data = {
            'records': data,
            'self': self.read()[0]
        }
        return data

    def action_print_sales_price_difference_report(self):
        report_data = self.get_sales_price_difference_report_data()
        return self.env.ref('pos_sale_report.sales_price_difference_report').with_context(landscape=True).report_action( self, data=report_data)

    def action_print_sales_price_difference_report_csv(self):
        report_data = self.get_sales_price_difference_report_data()
        if not report_data['records']:
            logger.info(f"No data")
            return {
                'warning': {
                    'title': 'No Data',
                    'message': 'There is no data to export.',
                },
            }
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(report_data['records'][0].keys())
        for record in report_data['records']:
            writer.writerow(record.values())
        content = output.getvalue().encode('utf-8')
        filename = 'SalesPriceDifference.csv'
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id={}&filename={}&field=datas&download=true&filename={}'.format(
                self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.b64encode(content),
                    'mimetype': 'text/csv'
                }).id,
                filename,
                filename
            ),
            'target': 'new'
        }
