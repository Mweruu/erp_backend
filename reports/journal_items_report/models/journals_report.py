from odoo import models, fields, api
from datetime import datetime
import logging
import csv
import io
import base64
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JournalsReport(models.Model):
    _name = 'journal.items.report'
    _report_type = 'csv'

    @api.model
    def _default_type(self):
        journals = self.env['account.journal'].search(
            [('company_id', '=', self.env.company.id), ('type', 'in', ['bank', 'cash'])])
        return [(journal.id, journal.name) for journal in journals]

    journal_type = fields.Selection(selection=_default_type, string='Journal Type')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_journals(self):
        data = []
        entries = self.env['account.move.line'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('journal_id.id', '=', self.journal_type),
            ('amount_currency', '>', 0),
            ('parent_state', '=', 'posted')
        ])
        grand_total = round(sum(entry.amount_currency for entry in entries), 2)

        for entry in entries:
            journal_entry = entry['move_id']
            formatted_amount = '{:,.2f}'.format(entry['amount_currency'])

            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = entry['create_date'].astimezone(local_tz)
            if journal_entry:
                data.append({
                    'Datetime': local_create_date.strftime('%d-%m-%Y, %H:%M:%S'),
                    'Journal Entry': entry['move_id'].name,
                    'Label': entry['name'],
                    'Customer': entry['partner_id'].name,
                    'Amount': formatted_amount,
                })

        data = {
            'records': data,
            'grand_total': grand_total,
            'self': self.read()[0],
            'account_name': self.journal_type
        }

        return data

    def action_print_journal_items_report(self):
        report_data = self.get_journals()
        return self.env.ref('journal_items_report.journal_items_report').with_context(landscape=True).report_action(None,
                                                                                                        data=report_data)

    def action_print_journal_items_csv(self):
        report_data = self.get_journals()
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
        filename = 'statementReport.csv'
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
