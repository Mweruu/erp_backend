from odoo import models, fields, api
from datetime import datetime
import logging
import csv
import io
import base64
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PhonePaymentReport(models.Model):
    _name = "phone.payment.report"
    _report_type = 'csv'
    _description = "Phone Payment tax"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_phone_payment(self):
        data = []
        grand_total = 0
        payments = self.env['dk.phone.payment'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
        ])
        for payment in payments:

            phone_payment_lines = self.env['dk.phone.payment.line'].search([('phone_payment_id', '=', payment.id)])
            for line in phone_payment_lines:
                local_tz = pytz.timezone('Etc/GMT-3')
                local_create_date = payment['create_date'].astimezone(local_tz)
                total = round(line['amount'], 2)
                grand_total += total
                if local_create_date:
                    data.append({
                        'Datetime': local_create_date.strftime('%d-%m-%Y'),
                        'Name': payment['name'],
                        'Amount': line['amount']
                    })

        sorted_data = sorted(data, key=lambda time: time['Datetime'], reverse=True)
        data = {
            'records': sorted_data,
            'grand_total': grand_total,
            'self': self.read()[0],
        }
        return data

    def action_print_phone_payment_report(self):
        report_data = self.get_phone_payment()
        return self.env.ref('dk_phone_payment.phone_payment_report').with_context(landscape=True).report_action(None,
                                                                                                                data=report_data)

    def action_print_phone_payment_csv(self):
        report_data = self.get_phone_payment()
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
        filename = 'PhonePayment.csv'
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
