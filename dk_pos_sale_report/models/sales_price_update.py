import base64
import csv
import io
from datetime import datetime

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PriceDifference(models.Model):
    _name = "sales.price.differences"
    _description = "sale price differences"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())
    user_id = fields.Many2one('res.users', required=True, default=_default_user)

    def get_sales_price_difference_report_data(self):
        data = []
        query = """
            select spd.create_date as time, rp."name" as username, pt."name" ->> 'en_US' as product, spd.old_price as old_price,spd.list_price as list_price
            from sales_price_difference as spd
                JOIN product_product as pp ON pp.id = spd.product_id
                JOIN product_template as pt ON pp.product_tmpl_id = pt.id
                JOIN res_users  as ru ON ru.id = spd.create_uid
                JOIN res_partner as rp ON rp.id = ru.partner_id 
                where date(spd.create_date)  >= %s and date(spd.create_date ) <= %s
        """
        self.env.cr.execute(query, (self.date_from, self.date_to,))
        sales_price_differences = self.env.cr.fetchall()
        for sales_price_difference in sales_price_differences:
            product_name = sales_price_difference[2]
            user_name = sales_price_difference[1]
            old_price = sales_price_difference[3]
            list_price = sales_price_difference[4]
            diff = int(float(list_price)) - int(float(old_price))
            if product_name:
                data.append({
                    "User_id": user_name,
                    'Product_id': product_name,
                    "Old Price": old_price,
                    "Sales Price": list_price,
                    'Price Difference': diff,
                    'Time': sales_price_difference[0].strftime('%m-%d-%Y, %H:%M:%S'),
                })
        data = {
            'records': data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_sales_price_difference_report(self):
        report_data = self.get_sales_price_difference_report_data()
        return self.env.ref('dk_pos_sale_report.sales_price_difference_report').with_context(
            landscape=True).report_action(self, data=report_data)

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
