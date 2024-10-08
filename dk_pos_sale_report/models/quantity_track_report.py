import base64
from datetime import datetime

from odoo import models, fields, api
import logging
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QuantityTrackReport(models.Model):
    _name = "quantity.track.report"
    _report_type = 'csv'
    _description = "quantity track report"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_quantity_report_data(self):
        data = []
        query = """	
            select qt.create_date as create_date , pt.name->>'en_US' as product_id, rp.name as create_uid , qt."location" as "location" ,
            qt.warehouse_name as wh_name, qt.company_name  as company_name , qt.new_quantity as new_quantity , qt.initial_quantity as initial_quantity  from quantity_track as qt
                JOIN product_product as pp ON pp.id = qt.product_id
                JOIN product_template as pt ON pp.product_tmpl_id = pt.id
                JOIN res_users  as ru ON ru.id = qt.create_uid
                JOIN res_partner as rp ON rp.id = ru.partner_id 
            where date(qt.create_date)  >= %s and date(qt.create_date)  <= %s
        """

        self.env.cr.execute(query, (self.date_from, self.date_to,))
        quantities = self.env.cr.fetchall()
        for quantity in quantities:
            product_id = quantity[1]
            q1 = quantity[6]
            q2 = quantity[7]
            diff = int(float(q1)) - int(float(q2))
            if product_id:
                data.append({
                    'Datetime': quantity[0].strftime('%m-%d-%Y'),
                    'Product_id': quantity[1],
                    'User_id': quantity[2],
                    'Location': quantity[3],
                    'Warehouse': quantity[4],
                    'Company name': quantity[5],
                    'New Quantity': quantity[6],
                    'Initial quantity': quantity[7],
                    'Total difference': diff,
                })

        data = {
            'records': data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_quantity_report(self):
        report_data = self.get_quantity_report_data()
        return self.env.ref('dk_pos_sale_report.quantity_track_report').with_context(landscape=True).report_action(None,
                                                                                                                   data=report_data)

    def action_print_quantity_report_csv(self):
        report_data = self.get_quantity_report_data()
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
        filename = 'QuantityTrack.csv'
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
