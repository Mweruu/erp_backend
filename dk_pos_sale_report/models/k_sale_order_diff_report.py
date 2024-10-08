import base64
import csv
import io
from datetime import datetime

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)


class POSDifferenceReport(models.Model):
    _name = "sale.order.report.diffs"
    _description = "sale price difference"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_price_difference_report_data(self):
        data = []
        total = 0
        query = """
            select DATE(sol.create_date) as date,rp2."name"  as user, sol.order_id  as order_id, rp."name"  as partner_ref, so."name" as saleorder, pt.name->>'en_US' as product,
                pt.list_price as list_price, sol.price_unit  as price_unit,
                sol.product_uom_qty as in_qty, pp.id as product_id from sale_order_line as sol
                JOIN product_product as pp ON pp.id = sol.product_id
                JOIN product_template as pt ON pp.product_tmpl_id = pt.id 
                JOIN res_partner as rp ON rp.id = sol.order_partner_id
                JOIN res_users  as ru ON ru.id = sol.salesman_id  
                JOIN res_partner as rp2 ON rp2.id = ru.partner_id
                JOIN sale_order as so ON so.id = sol.order_id  
                where date(sol.create_date) >= %s and date(sol.create_date) <= %s 
                and sol.price_unit >= '0'
                and (sol.create_uid = CASE WHEN %s::boolean THEN %s::integer ELSE sol.create_uid END)
        """
        self.env.cr.execute(query, (self.date_from, self.date_to, self.user_id.id, self.user_id.id,))
        order_lines = self.env.cr.fetchall()
        for order_line in order_lines:
            # create a datamodel
            if order_line[7] != order_line[6]:
                date = order_line[0].strftime('%m-%d-%Y')
                user = order_line[1]
                customer = order_line[3]
                pos_no = order_line[4]
                product_id = order_line[5]
                fixed = order_line[6]
                sale = order_line[7]
                qty = order_line[8]
                diff = round(sale - fixed, 2)
                tot = round(diff * qty, 2)
                total += tot
                data.append({
                    'date': date,
                    'user': user,
                    'customer': customer,
                    'pos_no': pos_no,
                    'product_id': product_id,
                    'qty': qty,
                    'sale': sale,
                    'fixed': fixed,
                    'diff': diff,
                    'tot': tot
                }
                )

        # sort
        sorted_data = sorted(data, key=lambda tot: tot['tot'])

        data = {
            'records': sorted_data,
            'grand_total': round(total, 2),
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_difference_report(self):
        report_data = self.get_price_difference_report_data()
        return self.env.ref('dk_pos_sale_report.k_sale_orders_transactions_report').with_context(landscape=True). \
            report_action(self, data=report_data)

    def action_print_difference_report_csv(self):
        report_data = self.get_price_difference_report_data()
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
        filename = 'SaleDifferenceReport.csv'
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
