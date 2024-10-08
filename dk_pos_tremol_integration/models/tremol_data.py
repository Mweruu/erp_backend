from datetime import datetime
import base64
from odoo import models, fields, api
import logging
import csv
import io
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TremolData(models.Model):
    _name = "tremol.data"
    _description = "tremol data"

    date = fields.Date(default=datetime.now())

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_tremol_data_report_data(self):
        data = []
        total = 0
        tremol_data = []
        tremol_data += [b'\x6D']

        for t_data in tremol_data:
            print(t_data[0])
            data.append({
                'Datetime':t_data[0]
            })

        data = {
            'records': data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'total': total
        }
        return data

    def action_print_tremol_data_report(self):
        report_data = self.get_tremol_data_report_data()
        return self.env.ref('dk_pos_tremol_integration.tremol_data').with_context(landscape=True). \
            report_action(None, data=report_data)

    def action_print_tremol_data_report_csv(self):
        report_data = self.get_tremol_data_report_data()
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
        # grand_total_row = [''] * (len(header_row) - 1) + [report_data['total']]  # Fill empty columns with ''
        # writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'TremolData.csv'
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
