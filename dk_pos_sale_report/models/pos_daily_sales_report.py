import base64
from datetime import datetime

from odoo import models, fields, api
import logging
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PosDaily_Report(models.Model):
    _name = "pos.order.daily_report.report"
    _report_type = 'csv'
    _description = "pos order daily report"

    date = fields.Date(default=datetime.now())
    tot = fields.Float(string="Total", readonly=True)
    total_refunds = fields.Float(string="Total Refunds", readonly=True)
    total_rewards = fields.Float(string="Total Rewards", readonly=True)
    salesperson = fields.Many2one('res.users', string="SalesPerson", readonly=True)

    def get_pos_order_daily_report_data(self):
        query = """
            SELECT
                date(pol.create_date),
                sum(CASE WHEN pol.price_subtotal_incl > 0 THEN pol.price_subtotal_incl ELSE 0 end) _sum,
                sum(CASE WHEN pol.price_subtotal_incl < 0 and pol.is_reward_line is not TRUE   THEN pol.price_subtotal_incl ELSE 0 end) _refunds,
                sum(CASE WHEN pol.price_subtotal_incl < 0 and pol.is_reward_line = TRUE THEN pol.price_subtotal_incl ELSE 0 end) _gift_card_buy,
                rp."name",
                sum(CASE WHEN pol.order_id in (	
                SELECT 
                    loyalty_card.source_pos_order_id  
                FROM 
                    loyalty_card
                WHERE 
                    date(loyalty_card.create_date) = %s
                    AND loyalty_card.program_id = (
                        SELECT 
                            id 
                        FROM 
                            loyalty_program 
                        WHERE 
                            loyalty_program.program_type = 'gift_card'
                            )
                ) THEN pol.price_unit ELSE 0 end) _reward_line_sum
            FROM pos_order_line as pol
            JOIN res_users  as ru ON ru.id  = pol.create_uid
            JOIN res_partner as rp ON rp.id = ru.partner_id
            WHERE date(pol.create_date) = %s
            GROUP BY date(pol.create_date), rp."name"        
        """
        self.env.cr.execute(query, (self.date, self.date,))
        results = self.env.cr.fetchall()
        data = []
        all_sales_total = 0
        gc_grand_total = 0
        refunds_total = 0
        sales_total = 0
        coupons_total = 0
        for result in results:
            if len(result) > 0:
                total = result[1]
                refunds = result[2]
                coupons = result[3]
                user = result[4]
                gc_total = result[5]
                total_sales = round(total + refunds + coupons, 2)
                all_sales_total += total_sales
                gc_grand_total += gc_total
                refunds_total += refunds
                sales_total += total
                coupons_total += coupons
                data.append({
                    'salesperson': user,
                    'tot': total,
                    'total_refunds': refunds,
                    'total_rewards': coupons,
                    'gc_total': gc_total,
                    'Total Sales': total_sales
                })
        data = {
            'records': data,
            'date': self.date,
            'gc_grand_total': gc_grand_total,
            "all_sales_total": all_sales_total,
            "refunds_total": refunds_total,
            "sales_total": sales_total,
            "coupons_total": coupons_total
        }
        return data

    def action_print_pos_order_daily_report(self):
        report_data = self.get_pos_order_daily_report_data()
        return self.env.ref('dk_pos_sale_report.pos_order_daily_report').with_context(landscape=True).report_action(
            None,
            data=report_data)

    def action_print_pos_order_daily_report_csv(self):
        report_data = self.get_pos_order_daily_report_data()
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
        grand_total_row = ['Total'] + [report_data['sales_total']] + [report_data['refunds_total']] + [
            report_data['coupons_total']] + [report_data['gc_grand_total']] + [
                              report_data['all_sales_total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'POSdailysalesoverview.csv'
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
