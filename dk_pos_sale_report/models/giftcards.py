from datetime import datetime
import base64
from odoo import models, fields, api
import logging
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GiftCards(models.Model):
    _name = "gift.cards.report"
    _description = "gift cards"

    date = fields.Date(default=datetime.now())

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_gift_cards_report_data(self):
        data = []

        query = """
            select lc.create_date as create_date, lc.code as code, rp."name" as partner,rc."name" as company_name , lc.points as points from loyalty_card as lc
                left JOIN res_partner as rp ON rp.id = lc.partner_id 
                JOIN loyalty_program as lp ON lp.id = lc.program_id
                JOIN res_company as rc ON rc.id = lc.company_id  
                where date(lc.create_date) >= %s and date(lc.create_date) <= %s  
                and lp.program_type = 'gift_card'
        """
        self.env.cr.execute(query, (self.date_from, self.date_to,))
        cards = self.env.cr.fetchall()
        for card in cards:
            points = '{:,.2f}'.format(card[4])
            data.append({
                'Datetime': card[0].strftime('%m-%d-%Y, %H:%M:%S'),
                'Code': card[1],
                'Partner': card[2],
                'Company': card[3],
                'Balance': points,
            })

        sorted_data = sorted(data, key=lambda time: time['Datetime'], reverse=True)

        data = {
            'records': sorted_data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_gift_cards_report(self):
        report_data = self.get_gift_cards_report_data()
        return self.env.ref('dk_pos_sale_report.gift_cards_report').with_context(landscape=True). \
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
