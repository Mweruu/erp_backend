from odoo import models, fields, api
from datetime import datetime
import logging
import csv
import io
import base64
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WithholdingTax(models.Model):
    _name = 'withholding.tax.report'
    _report_type = 'csv'
    _description = "Withholding Tax report"

    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
    ], store=True, copy=False)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_withholding_tax(self):
        data = []
        wht_tax_group = self.env['account.tax.group'].search([('name', '=', 'Withholding Tax')])
        WHTtaxes = self.env['account.move.line'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('tax_group_id', '=', wht_tax_group.id),
            ('parent_state', '=', 'posted'),
        ])
        if self.partner_type == 'customer':
            WHTtaxes = WHTtaxes.filtered(lambda tax: tax.move_type in ['out_invoice', 'out_refund'])
        elif self.partner_type == 'supplier':
            WHTtaxes = WHTtaxes.filtered(lambda tax: tax.move_type in ['in_invoice', 'in_refund'])

        grand_total = round(sum(tax.amount_currency for tax in WHTtaxes), 2)

        for tax in WHTtaxes:
            journal_entry = tax['move_id']
            formatted_amount = '{:,.2f}'.format(tax['amount_currency'])
            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = tax['create_date'].astimezone(local_tz)
            if journal_entry:
                data.append({
                    'Datetime': local_create_date.strftime('%m-%d-%Y, %H:%M:%S'),
                    'Journal Entry': tax['move_name'],
                    'Customer': tax['partner_id'].name,
                    'Label': tax['name'],
                    'Amount': formatted_amount,
                })

        data = {
            'records': data,
            'grand_total': grand_total,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'partner_type': self.partner_type
        }
        return data

    def action_print_withholding_tax_report(self):
        report_data = self.get_withholding_tax()
        return self.env.ref('dk_withholding_tax_report.withholding_tax_report').with_context(
            landscape=True).report_action(
            None,
            data=report_data)

    def action_print_withholding_tax_csv(self):
        report_data = self.get_withholding_tax()
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
        # writer.writerow(report_data['records'][0].keys())
        for record in report_data['records']:
            writer.writerow(record.values())
        # # Write grand_total row
        grand_total_row = [''] * (len(header_row) - 1) + [report_data['grand_total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'Withholdingtax.csv'
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
