import base64
import csv
import io
import logging
from datetime import datetime

from odoo import models, fields, api

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class POSDifferenceReport(models.Model):
    _name = "pos.order.report.diffs"
    _description = "difference report"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_difference_report_data(self):
        data = []
        total = 0
        query = """ 
            select DATE(pol.create_date) as date, pol.order_id  as order_id, rp."name"  as partner_ref, po."name" as saleorder, pt.name->>'en_US' as product,
                pt.list_price as list_price, pol.price_unit  as price_unit,
                pol.qty as in_qty, pp.id as product_id from pos_order_line as pol
                JOIN product_product as pp ON pp.id = pol.product_id
                JOIN product_template as pt ON pp.product_tmpl_id = pt.id 
                JOIN res_users  as ru ON ru.id = pol.create_uid 
                JOIN res_partner as rp ON rp.id = ru.partner_id 
                JOIN pos_order as po ON po.id = pol.order_id  
                where date(pol.create_date) >= %s
                and date(pol.create_date) <= %s
                AND (pol.create_uid = CASE WHEN %s::boolean THEN %s::integer ELSE pol.create_uid END)
                and pol.is_reward_line is not TRUE 
                and pol.product_id in (
                    SELECT 
                        product_product.id  
                    FROM 
                        product_product
                    WHERE 
                        product_product.product_tmpl_id  not in (
                        SELECT 
                            product_template.id  
                        FROM 
                            product_template
                        WHERE 
                            product_template.type = 'service'
                    )
                )
        """
        self.env.cr.execute(query, (self.date_from, self.date_to, self.user_id.id, self.user_id.id,))
        order_lines = self.env.cr.fetchall()
        for order_line in order_lines:
            if order_line[5] != order_line[6]:
                date = order_line[0].strftime("%m-%d-%Y")
                user = order_line[2]
                parts = user.split()
                initials = [part[0] for part in parts]
                abbreviated = " ".join(initials)
                pos_no = order_line[3]
                product_id = order_line[4]
                qty = order_line[7]
                sale = order_line[6]
                fix = order_line[5]
                fixed = round(fix, 2)
                diff = round(sale - fixed, 2)
                tot = round(diff * qty, 2)
                total += tot
                data.append({
                    'date': date,
                    'user': abbreviated,
                    'pos_no': pos_no,
                    'product_id': product_id,
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
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_difference_report(self):
        report_data = self.get_difference_report_data()
        return self.env.ref('dk_pos_sale_report.k_pos_orders_transactions_report').with_context(
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
        filename = 'PosDifferenceReport.csv'
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
