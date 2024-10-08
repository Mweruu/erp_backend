import base64
from datetime import datetime

from odoo import models, fields, api
import logging
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QuantityTrackReport(models.Model):
    _name = "internal.expense.report"
    _report_type = 'csv'
    _description = "internal expense report"

    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_internal_expense_report_data(self):
        data = []
        total = 0
        total_for_account = 0
        account_data = []
        query = """
        select icl.create_date , aa."name", pt.name->>'en_US' as product_id, icl.product_qty , icl.list_price ,icl.unit_price, icl.standard_price from internal_consumption_lines as icl
            join account_account as aa on aa.id = icl.account
            join product_product pp on pp.id = icl.product_id 
            join product_template pt on pt.id = pp.product_tmpl_id 
            where date(icl.create_date) >=  %s and date(icl.create_date) <= %s
        """
        self.env.cr.execute(query, (self.date_from, self.date_to,))
        expenses = self.env.cr.fetchall()
        unique_account_numbers = set()
        for expense in expenses:
            unique_account_numbers.add(expense[1])
            product_id = expense[2]
            price_unit = expense[5] if expense[5] is not None else 0.0
            total += price_unit
            if product_id:
                data.append({
                    'Datetime': expense[0].strftime('%m-%d-%Y %H:%M:%S'),
                    'account': expense[1],
                    'product': expense[2],
                    'quantity': expense[3],
                    'list_price': expense[4],
                    'standard_price': expense[6],
                    'price_unit': price_unit,
                })
        unique_values_list = list(unique_account_numbers)
        for account_name in unique_values_list:
            query = """
            select  icl.create_date ,aa."name", pt.name->>'en_US' as product_id, icl.product_qty , icl.list_price ,icl.unit_price from internal_consumption_lines as icl
                join account_account as aa on aa.id = icl.account
                join product_product pp on pp.id = icl.product_id 
                join product_template pt on pt.id = pp.product_tmpl_id 
                where date(icl.create_date)  >= %s and date(icl.create_date)  <= %s 
                and aa."name" = %s
            """
            self.env.cr.execute(query, (self.date_from, self.date_to, account_name,))
            expense_account = self.env.cr.fetchall()
            total_amount = sum(e[5] for e in expense_account if e[5] is not None)
            total_for_account += total_amount
            account_data.append({
                'account': account_name if account_name else 'Other Devices',
                'total_amount': total_amount
            })
        sorted_data = sorted(data, key=lambda time: time['Datetime'], reverse=True)

        data = {
            'records': sorted_data,
            'acc_records': account_data,
            'Total': total,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_internal_expense_report(self):
        report_data = self.get_internal_expense_report_data()
        return self.env.ref('internal_consumption.internal_expense_report').with_context(landscape=True).report_action(
            None,
            data=report_data)

    def action_print_internal_expense_report_csv(self):
        report_data = self.get_internal_expense_report_data()
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
        grand_total_row = [''] * (len(header_row) - 1) + [report_data['Total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'InternalExpense.csv'
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
