import base64
import csv
import io
import logging
import re
from datetime import datetime, time

import pytz
from odoo import models, fields, api

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class POSDifferenceReport(models.Model):
    _name = "pos.order.report.diffs"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_difference_report_data(self):
        data, domain = [], []
        total = 0
        if self.date_from:
            domain += [('create_date', '>=', self.date_from)]
        if self.date_to:
            # convert to datatime
            dt = datetime.combine(self.date_to, time(hour=23, minute=59, second=59))
            domain += [('create_date', '<=', dt)]
        if self.user_id:
            domain += [('user_id', '=', self.user_id.id)]

        pos = self.env['pos.order'].search(domain)
        po_ids = [po.id for po in pos]
        domain += [('price_unit', ">=", 0)]
        orders = self.env['pos.order.line'].search([('order_id', '=', po_ids)])
        for order in orders:
            # create a datamodel
            product = self.env['product.product'].search_read([('id', '=', order.product_id.id)])[0]
            if not order.price_unit == product['lst_price']:
                local_tz = pytz.timezone('Etc/GMT-3')
                local_create_date = order['create_date'].astimezone(local_tz)
                date = local_create_date.strftime('%d-%m-%Y')
                domain += [('id', '=', [0])]
                user, pos_no = '', ''
                for po in pos:
                    if po.id == order.order_id.id:
                        user = po.user_id.name
                        parts = user.split()
                        initials = [part[0] for part in parts]
                        abbreviated = " ".join(initials)
                        pos_no = po.pos_reference

                if user == '' or pos_no == '':
                    continue

                product_id = product['partner_ref']
                pattern = re.compile(r'\[.*?\]')
                result = re.sub(pattern, '', product_id)
                qty = order['qty']
                sale = order['price_unit']
                fix = product['lst_price']
                fixed = round(fix, 2)
                diff = round(sale - fixed, 2)
                tot = round(diff * qty, 2)
                total += tot
                logger.debug(f"sale: {sale}, fixed:{fixed}, qty:{qty},difference: {diff},tot: {tot}")
                data.append({
                    'date': date,
                    'user': abbreviated,
                    'pos_no': pos_no,
                    'product_id': result,
                    'qty': qty,
                    'sale': sale,
                    'fixed': fixed,
                    'diff': diff,
                    'tot': tot
                })

        sorted_data = sorted(data, key=lambda tot: tot['tot'])

        data = {
            'records': sorted_data,
            'grand_total': round(total, 2),
            'self': self.read()[0]
        }
        return data

    def action_print_difference_report(self):
        report_data = self.get_difference_report_data()
        return self.env.ref('pos_sale_report.k_pos_orders_transactions_report').with_context(
            landscape=True).report_action(self, data=report_data)

    def action_print_difference_report_csv(self):
        report_data = self.get_difference_report_data()
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
        filename = 'KposReport.csv'
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
