import base64
import re
import logging
from datetime import datetime

from odoo import models, fields, api
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class POSDifferenceReport(models.Model):
    _name = "pos.order.report.refunds"
    _description = "orderline refunds report"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_refunds_report_data(self):
        data = []
        total = 0

        query = """
            select DATE(pol.create_date) as date, po.pos_reference  as order_ref, rp."name" as name, pt.name->>'en_US' as product,
             pol.qty as in_qty, pol.price_unit  as price_unit, pol.price_subtotal_incl  as total, 
                pp.id as product_id from pos_order_line as pol
                JOIN product_product as pp ON pp.id = pol.product_id
                JOIN product_template as pt ON pp.product_tmpl_id = pt.id 
                JOIN res_users  as ru ON ru.id = pol.create_uid 
                JOIN res_partner as rp ON rp.id = ru.partner_id 
                JOIN pos_order as po ON po.id = pol.order_id  
                where date(pol.create_date) >= %s
                and date(pol.create_date) <= %s
                AND (po.user_id = CASE WHEN %s::boolean THEN %s::integer ELSE po.user_id END)
                and pol.qty < '0'
        """

        self.env.cr.execute(query, (self.date_from, self.date_to, self.user_id.id, self.user_id.id,))
        order_lines = self.env.cr.fetchall()
        for order_line in order_lines:
            date = order_line[0].strftime('%m-%d-%Y')
            user = order_line[2]
            pos_no = order_line[1]
            product_id = order_line[3]
            pattern = re.compile(r'\[.*?\]')
            result = re.sub(pattern, '', product_id)
            qty = order_line[4]
            sale = round(order_line[5], 2)
            # fixed = round(product['list_price'], 2)
            # tot = round(sale * qty, 2)
            tot = round(order_line[6], 2)
            total += tot

            data.append({
                'date': date,
                'user': user,
                'pos_no': pos_no,
                'product_id': result,
                'qty': qty,
                'sale': sale,
                # 'fixed': fixed,
                'tot': tot
            })
        sorted_data = sorted(data, key=lambda time: time['date'], reverse=True)

        data = {
            'records': sorted_data,
            'grand_total': round(total, 2),
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_refunds_report(self):
        report_data = self.get_refunds_report_data()
        return self.env.ref('dk_pos_sale_report.k_pos_refunds_transactions_report').with_context(
            landscape=True).report_action(self, data=report_data)

    def action_print_refunds_report_csv(self):
        report_data = self.get_refunds_report_data()
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
        filename = 'OrderlineRefundsReport.csv'
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
