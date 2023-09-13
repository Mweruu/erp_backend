import csv
import io
from datetime import datetime

import pytz
from odoo import models, fields, api
import base64

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PurchaseReport(models.Model):
    _name = "purchase.order.report"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_purchase_report_data(self):
        data = []
        total = 0
        purchases = self.env['purchase.order'].search([('partner_id', '=', self.partner_id.id),
                                                       ('create_date', '>=', self.date_from),
                                                       ('create_date', '<=', self.date_to),
                                                       ])
        for purchase in purchases:
            order_line_items = self.env['purchase.order.line'].search_read([('order_id', '=', purchase.id)])
            for order_line_item in order_line_items:
                local_tz = pytz.timezone('Etc/GMT-3')
                local_create_date = order_line_item['create_date'].astimezone(local_tz)
                Amount = order_line_item['price_total']
                total += Amount
                data.append({
                    'Purchase_order_ref': purchase.name,
                    'Product_id': order_line_item['name'],
                    'Quantity': order_line_item['product_qty'],
                    'Datetime': local_create_date.strftime('%d-%m-%Y, %H:%M:%S'),
                    'Price': order_line_item['price_unit'],
                    'Amount': order_line_item['price_total'],

                })

        data = {
            'records': data,
            'grand_total': round(total, 2),
            'self': self.read()[0]
        }
        return data

    def action_print_purchase_report(self):
        report_data = self.get_purchase_report_data()
        return self.env.ref('pos_sale_report.purchase_order_report').with_context(
            landscape=True).report_action(self, data=report_data)

    def action_print_purchase_report_csv(self):
        report_data = self.get_purchase_report_data()
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
        header_row = report_data['records'][0].keys()
        writer.writerow(header_row)
        for record in report_data['records']:
            writer.writerow(record.values())
        grand_total_row = [''] * (len(header_row) - 1) + [report_data['grand_total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'PurchaseReport.csv'
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
