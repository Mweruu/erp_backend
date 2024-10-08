import base64
import logging
from datetime import datetime

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
        data = []
        grand_total = 0

        query = """
            select DATE(po.create_date) as date, po.pos_reference  as order_ref, rp."name" as name,
            po.amount_total  as total from pos_order as po
            JOIN res_users  as ru ON ru.id = po.create_uid 
            JOIN res_partner as rp ON rp.id = ru.partner_id 
            where date(po.create_date) >= %s
            and date(po.create_date) <= %s
            AND (po.user_id = CASE WHEN %s::boolean THEN %s::integer ELSE po.user_id END)
            and po.amount_total  < '0'
        """
        self.env.cr.execute(query, (self.date_from, self.date_to, self.user_id.id, self.user_id.id,))
        orders = self.env.cr.fetchall()

        for order in orders:
            date = order[0].strftime('%m-%d-%Y')
            user = order[2]
            pos_no = order[1]
            total = round(order[3], 2)
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
            'grand_total': round(grand_total, 2),
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_refunded_orders_report(self):
        report_data = self.get_refunded_orders_report_data()
        return self.env.ref('dk_pos_sale_report.k_pos_refunded_orders_transactions_report').with_context(
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
