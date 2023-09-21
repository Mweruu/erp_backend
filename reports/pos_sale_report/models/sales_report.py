from odoo import models, fields, api
from datetime import datetime
import base64
import csv
import io

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
import locale

# Set the locale to the user's default
locale.setlocale(locale.LC_ALL, '')


class Sales(models.Model):
    _name = 'sales.reports'
    _description = "Sales report"

    date = fields.Date(default=datetime.now())

    def get_sales_report_data(self):
        data = []

        invoices = self.env['account.move'].search([('invoice_date', '=', self.date)])

        for invoice in invoices:
            amount = invoice['amount_total_in_currency_signed']
            currency_format = "{:,.2f}".format(amount)
            data.append({
                "Sale_no": invoice['payment_reference'],
                "Partner": invoice['invoice_partner_display_name'],
                "Amount": currency_format,
            })

        data = {
            'records': data,
            'self': self.read()[0]
        }
        return data

    def action_print_sales_report(self):
        report_data = self.get_sales_report_data()
        return self.env.ref('pos_sale_report.sales_report').with_context(landscape=True).report_action(self,
                                                                                                       data=report_data)

    def action_print_sales_report_csv(self):
        report_data = self.get_sales_report_data()
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
        writer.writerow(report_data['records'][0].keys())
        for record in report_data['records']:
            writer.writerow(record.values())
        content = output.getvalue().encode('utf-8')
        filename = 'Sales.csv'
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
