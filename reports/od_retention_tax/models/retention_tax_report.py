from odoo import models, fields, api
from datetime import datetime
import logging
import csv
import io
import base64
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RetentionTaxReport(models.Model):
    _name = "retention.tax.report"
    _report_type = 'csv'
    _description = "Retention tax"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_retention_tax(self):
        data = []
        retention_tax_value = self.env['ir.config_parameter'].sudo().get_param(
            'od_retention_tax.retention_tax_id')
        retention_tax_value_integer = int(retention_tax_value)

        acc_records = self.env['account.payment'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('tax_id', '=', retention_tax_value_integer)])
        account = self.env['account.tax'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('id', '=', retention_tax_value)])
        retention_account_id = account.retention_account_id.id

        items = self.env['account.move.line'].search([
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to),
                ('payment_id', 'in', acc_records.ids),
                ('account_id', '=', retention_account_id),
                ('amount_currency', '>', 0),
                ('parent_state', '=', 'posted')
            ])
        grand_total = round(sum(item.amount_currency for item in items), 2)
        for item in items:
            journal_entry = item['move_id']
            formatted_amount = '{:,.2f}'.format(item['amount_currency'])

            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = item['create_date'].astimezone(local_tz)
            if journal_entry:
                data.append({
                    'Datetime': local_create_date.strftime('%d-%m-%Y, %H:%M:%S'),
                    'Journal Entry': item['move_id'].name,
                    'Label': item['name'],
                    'Customer': item['partner_id'].name,
                    'Amount': formatted_amount,
                })
        sorted_data = sorted(data, key=lambda time: time['Datetime'], reverse=True)
        data = {
            'records': sorted_data,
            'grand_total': grand_total,
            'self': self.read()[0],
            'account_name': account.name
        }
        return data

    def action_print_retention_tax_report(self):
        report_data = self.get_retention_tax()
        return self.env.ref('od_retention_tax.retention_tax_report').with_context(landscape=True).report_action(None,
                                                                                                                data=report_data)

    def action_print_retention_tax_csv(self):
        report_data = self.get_retention_tax()
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
            # Write grand_total row
        grand_total_row = [''] * (len(header_row) - 1) + [report_data['grand_total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'RetentionTax.csv'
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
