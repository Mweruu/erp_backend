import csv
import io
from datetime import datetime

from odoo import models, fields, api
import base64

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PurchaseReport(models.Model):
    _name = "purchase.order.report"
    _description = "purchases report"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_purchase_report_data(self):
        data = []
        total = 0
        query = """
            select DATE(pol.create_date) as date, pol.order_id  as order_id, po."name" as order_ref, pt.name->>'en_US' as product,
                pol.product_qty  as in_qty, pol.price_unit  as price_unit, pol.price_total as total, 
                pp.id as product_id from purchase_order_line as pol
                JOIN product_product as pp ON pp.id = pol.product_id
                JOIN product_template as pt ON pp.product_tmpl_id = pt.id 
                JOIN res_users  as ru ON ru.id = pol.create_uid 
                JOIN res_partner as rp ON rp.id = ru.partner_id 
                JOIN purchase_order as po ON po.id = pol.order_id  
                where date(pol.create_date) >= %s  and date(pol.create_date)  <= %s
                AND (pol.partner_id = CASE WHEN %s::boolean THEN %s::integer ELSE pol.partner_id END)
          """
        self.env.cr.execute(query, (self.date_from, self.date_to, self.partner_id.id, self.partner_id.id,))
        order_lines = self.env.cr.fetchall()
        for order_line in order_lines:
            Amount = order_line[6]
            total += Amount
            data.append({
                'Purchase_order_ref': order_line[2],
                'Product_id': order_line[3],
                'Quantity': order_line[4],
                'Datetime': order_line[0].strftime('%m-%d-%Y'),
                'Price': order_line[5],
                'Amount': Amount,
            })

        data = {
            'records': data,
            'grand_total': round(total, 2),
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'partner_id': self.partner_id.name
        }
        return data

    def action_print_purchase_report(self):
        report_data = self.get_purchase_report_data()
        return self.env.ref('dk_pos_sale_report.purchase_order_report').with_context(
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
