import base64
import csv
import io
import re
from datetime import datetime
from datetime import time

import pytz
from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)


class POSDifferenceReport(models.Model):
    _name = "sale.order.report.diffs"
    _description = "Sale price difference"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_price_difference_report_data(self):
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

        pos = self.env['sale.order'].search(domain)
        po_ids = [po.id for po in pos]
        domain += [('price_unit', ">=", 0)]
        order_lines = self.env['sale.order.line'].search([('order_id', 'in', po_ids)])

        for order_line in order_lines:
            # create a datamodel
            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = order_line['create_date'].astimezone(local_tz)
            product = self.env['product.product'].search_read([('id', '=', order_line.product_id.id)])[0]

            if not order_line.price_unit == product['lst_price']:
                date = local_create_date.strftime('%d-%m-%Y, %H:%M:%S')
                domain_user += [('id', '=', [0])]
                pos_no = order_line.order_id.name
                user = order_line.order_id.user_id.name
                customer = order_line.order_id.partner_id.name
                product_id = product['partner_ref']
                pattern = re.compile(r'\[.*?\]')
                result = re.sub(pattern, '', product_id)
                qty = order_line.product_uom_qty
                sale = order_line.price_unit
                list_price = product['lst_price']
                difference = round(sale - list_price, 2)
                total = round(difference * qty, 2)
                grand_total += total
                logger.debug(f"sale: {sale}, list_price:{list_price}, qty:{qty},difference: {difference},total: {total}")
                data.append({
                    'date': date,
                    'user': user,
                    'customer': customer,
                    'pos_no': pos_no,
                    'product_id': result,
                    'qty': qty,
                    'sale': sale,
                    'list_price': list_price,
                    'difference': difference,
                    'total': total
                }
                )

        # sort
        sorted_data = sorted(data, key=lambda total: total['total'])

        data = {
            'records': sorted_data,
            'grand_total': round(grand_total, 2),
            'self': self.read()[0]
        }
        return data

    def action_print_difference_report(self):
        report_data = self.get_price_difference_report_data()
        return self.env.ref('pos_sale_report.k_sale_orders_transactions_report').with_context(landscape=True). \
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
        filename = 'DifferenceReport.csv'
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

    def sort_dict(data):
        sorted = True
