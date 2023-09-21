import base64
import re
import logging
from datetime import datetime, time

import pytz
from odoo import models, fields, api
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class OrderRefunds(models.Model):
    _name = "pos.order.refunds"
    _description = "Refunds"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_refunded_orders_report_data(self):
        data, domain, domain_user = [], [], []
        grand_total = 0
        if self.date_from:
            domain += [('create_date', '>=', self.date_from)]
        if self.date_to:
            # convert to datatime
            dt = datetime.combine(self.date_to, time(hour=23, minute=59, second=59))
            domain += [('create_date', '<=', dt)]

        if self.user_id:
            domain += [('user_id', '=', self.user_id.id)]

        domain += [('amount_total', '<', 0)]
        orders = self.env['pos.order'].search(domain)

        for order in orders:
            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = order['create_date'].astimezone(local_tz)
            date = local_create_date.strftime('%d-%m-%Y, %H:%M:%S')
            user = order.user_id.name
            pos_no = order['pos_reference']
            total = round(order['amount_total'], 2)
            grand_total += total
            data.append({
                'date': date,
                'user': user,
                'pos_no': pos_no,
                'total': total
            })
        sorted_data = sorted(data, key=lambda time: time['date'], reverse=True)
        data = {
            'records': sorted_data,
            'grand_total':  round(grand_total, 2),
            'self': self.read()[0]
        }
        return data

    def action_print_refunded_orders_report(self):
        report_data = self.get_refunded_orders_report_data()
        return self.env.ref('pos_sale_report.k_pos_refunded_orders_transactions_report').with_context(
            landscape=True).report_action(self, data=report_data)

    def action_print_refunded_orders_report_csv(self):
        report_data = self.get_refunded_orders_report_data()
        if not report_data['records']:
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
            # Write grand_total row
        grand_total_row = [''] * (len(header_row) - 1) + [report_data['grand_total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'OrderRefundsReport.csv'
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
