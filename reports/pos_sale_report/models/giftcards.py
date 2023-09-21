from datetime import datetime
import base64
from odoo import models, fields, api
import logging
import csv
import io
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GiftCards(models.Model):
    _name = "gift.cards.report"
    _description = "Gift Card Report"

    date = fields.Date(default=datetime.now())

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_gift_cards_report_data(self):
        data = []

        cards = self.env['gift.card'].search([('create_date', '>=', self.date_from),
                                              ('create_date', '<=', self.date_to),
                                              ])

        for card in cards:
            local_tz = pytz.timezone('Etc/GMT-3')
            local_create_date = card['create_date'].astimezone(local_tz)
            initial_amount = '{:,.2f}'.format(card['initial_amount'])
            balance = '{:,.2f}'.format(card['balance'])

            data.append({
                'Datetime': local_create_date.strftime('%d-%m-%Y, %H:%M:%S'),
                'Code': card['code'],
                'Partner': card['partner_id'].name,
                'Company': card['company_id'].name,
                'State': card['state'],
                'Initial amount': initial_amount,
                'Balance': balance,
            })

        data = {
            'records': data,
            'self': self.read()[0],
        }
        return data

    def action_print_gift_cards_report(self):
        report_data = self.get_gift_cards_report_data()
        return self.env.ref('pos_sale_report.gift_cards_report').with_context(landscape=True). \
            report_action(None, data=report_data)

    def action_print_gift_cards_report_csv(self):
        report_data = self.get_gift_cards_report_data()
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
        filename = 'GiftCards.csv'
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
