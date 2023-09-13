import base64
import csv
import io
from odoo import fields, api, models
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class KPurchaseReportWizard(models.TransientModel):
    _name = "purchase.kpurchase.wizard"
    _description = "KPurchase Report Wizard"

    partner = fields.Many2one('res.partner', string="Partner")

    date_from = fields.Datetime(default=datetime.now())
    date_to = fields.Datetime(default=datetime.now())

    def get_kpurchase_report_data(self):
        domain = []
        domain += [('partner_id', '=', self.partner.id)]
        if self.date_from:
            domain += [('create_date', '>=', self.date_from)]
        if self.date_to:
            domain += [('create_date', '<=', self.date_to)]

        transactions = self.env['purchase.kpurchase'].search_read(domain, order='id')
        data = {
            'form': self.read()[0],
            'transactions': transactions
        }
        return data

    def action_print_report(self):
        report_data = self.get_kpurchase_report_data()
        return (self.env.ref("kpartnerfleet.k_purchase_orders_transactions_report").with_context(landscape=True).
                report_action(self, data=report_data))

    def action_print_report_csv(self):
        data = []

        transactions = self.env['purchase.kpurchase'].search([('create_date', '>=', self.date_from),
                                                              ('create_date', '<=', self.date_to),
                                                              ])
        for transaction in transactions:
            data.append({
                'create_date': transaction['create_date'].strftime('%d-%m-%Y, %H:%M:%S'),
                'name': transaction['name'],
                'vehicle_id': transaction['vehicle_id'].name,
                'product': transaction['product'].name,
                'quantity': transaction['quantity'],
                'cost_price': transaction['cost_price'],
                'total_cost_price': transaction['total_cost_price']
            })

        report_data = self.get_kpurchase_report_data()
        if not report_data['transactions']:
            logger.info(f"No data")
            return {
                'warning': {
                    'title': 'No Data',
                    'message': 'There is no data to export.',
                },
            }
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(data[0].keys())
        for record in data:
            writer.writerow(record.values())
        content = output.getvalue().encode('utf-8')
        filename = 'KpurchaseReport.csv'
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
