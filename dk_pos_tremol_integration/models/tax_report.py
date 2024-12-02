from datetime import datetime
import base64
from odoo import models, fields, api
import logging
import csv
import io
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RaxReport(models.Model):
    _name = "tax.report"
    _description = "Total of the amount sent to TIMS"

    date = fields.Date(default=datetime.now())

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())
    sale_type = fields.Selection([('invoice', 'Invoice'), ('POS', 'POS')], 'Sale Type', default='POS')

    def get_tax_report_data(self):
        data = []
        total = 0
        if self.sale_type == 'POS':
            taxes = self.env['pos.order'].search([('create_date', '>=', self.date_from),
                                                  ('create_date', '<=', self.date_to),
                                                  ('manual_etr', '=', False)
                                                  ])

            for tax in taxes:
                local_tz = pytz.timezone('Etc/GMT-3')
                local_create_date = tax['create_date'].astimezone(local_tz)
                amount_total = round(tax['amount_total'], 2)
                amount_tax = round(tax['amount_tax'], 2)
                total += amount_tax

                data.append({
                    'Datetime': local_create_date.strftime('%m-%d-%Y, %H:%M:%S'),
                    'Receipt Number': tax['pos_reference'],
                    'Partner': tax['partner_id'].name,
                    'Total Amount': amount_total,
                    'Amount Tax': amount_tax,

                })

        if self.sale_type == 'invoice':
            query = """
                select am.create_date as create_date, am."name" ,rp."name" , am.amount_total_signed , am.amount_tax_signed 
                from account_move am 
                JOIN res_partner rp ON am.partner_id = rp.id 
                where date(am.create_date)  >= %s and date(am.create_date)  <= %s
                and am.move_type IN ('out_invoice', 'out_refund')
                and am.l10n_ke_cu_serial_number is not null 
            """
            self.env.cr.execute(query, (self.date_from, self.date_to,))
            taxes = self.env.cr.fetchall()
            for tax in taxes:
                local_tz = pytz.timezone('Etc/GMT-3')
                local_create_date = tax[0].astimezone(local_tz)
                amount_total = round(tax[3], 2)
                amount_tax = round(tax[4], 2)
                total += amount_tax

                data.append({
                    'Datetime': local_create_date.strftime('%m-%d-%Y, %H:%M:%S'),
                    'Receipt Number': tax[1],
                    'Partner': tax[2],
                    'Total Amount': amount_total,
                    'Amount Tax': amount_tax,

                })

        data = {
            'records': data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'total': total
        }
        return data

    def action_print_tax_report(self):
        report_data = self.get_tax_report_data()
        return self.env.ref('dk_pos_tremol_integration.tax_report').with_context(landscape=True). \
            report_action(None, data=report_data)

    def action_print_tax_report_csv(self):
        report_data = self.get_tax_report_data()
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
        grand_total_row = [''] * (len(header_row) - 1) + [report_data['total']]  # Fill empty columns with ''
        writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'Taxreport.csv'
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
