from odoo import models, fields, api
from datetime import datetime
import base64
import csv
import io

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
import locale

# Set the locale to the user's default
locale.setlocale(locale.LC_ALL, '')


class SourceLocation(models.Model):
    _name = 'diff.source.location.report'
    _description = "different source location report"

    date = fields.Date(default=datetime.now())
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_diff_source_location_report_data(self):
        data = []
        query = """
            select sp.scheduled_date, sp."name" as Name, sw.code, sl.complete_name, sp.origin, po.delay_picking from stock_picking as sp 
            JOIN pos_order po ON po.id = sp.pos_order_id
            JOIN pos_session ps ON ps.id = po.session_id  
            JOIN pos_config pc ON pc.id = ps.config_id  
            JOIN stock_warehouse sw ON sw.id = pc.warehouse_id 
            JOIN stock_location sl ON sl.id = sp.location_id 
            where date(sp.create_date) >= %s and date(sp.create_date) <= %s
            and sp.state = 'done'
            and sl.warehouse_id  != pc.warehouse_id
        """
        self.env.cr.execute(query, (self.date_from, self.date_to,))
        pickings = self.env.cr.fetchall()
        for p in pickings:
            data.append({
                "date": p[0],
                "Name": p[1],
                "Expected Shipping Location": p[2],
                "Source location": p[3],
                "Source Document": p[4],
                "ship later": p[5],
            })
        sorted_data = sorted(data, key=lambda time: time['date'], reverse=True)

        data = {
            'records': sorted_data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_diff_source_location_report(self):
        report_data = self.get_diff_source_location_report_data()
        return self.env.ref('dk_all_sales.diff_source_location_report').with_context(landscape=True).report_action(self,
                                                                                                          data=report_data)

    def action_print_diff_source_location_report_csv(self):
        report_data = self.get_diff_source_location_report_data()
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
        filename = 'diffsourcelocation.csv'
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
