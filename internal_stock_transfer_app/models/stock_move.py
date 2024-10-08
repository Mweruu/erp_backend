from odoo import models, fields, api
from datetime import datetime
import logging
import csv
import io
import base64

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class StockMove(models.Model):
    _name = 'internal.stock.move.report'
    _report_type = 'csv'
    _description = "Statement report"

    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_moves(self):
        data = []
        query = """
             select sm."date" , sm.reference,pt.name->>'en_US' as product , slt.complete_name  as loc_from, sl.complete_name  as loc_to, sm.quantity_done from stock_move sm
                JOIN stock_location as sl on sl.id = sm.location_dest_id
                JOIN stock_location as slt on slt.id = sm.location_id
                JOIN product_product as pp ON pp.id = sm.product_id
	            JOIN product_template as pt ON pp.product_tmpl_id = pt.id
                where date(sm."date") >= %s and date(sm."date") <= %s and sm.stock_transfer_id is not null
         """
        self.env.cr.execute(query, (self.date_from, self.date_to,))
        moves = self.env.cr.fetchall()
        for move in moves:
            data.append({
                'Datetime': move[0].strftime('%m-%d-%Y, %H:%M:%S'),
                'reference': move[1],
                'product': move[2],
                'location_id': move[3],
                'location_dest_id': move[4],
                'quantity_done': move[5]
            })
        sorted_data = sorted(data, key=lambda time: time['Datetime'], reverse=True)
        data = {
            'records': sorted_data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
        }
        return data

    def action_print_stock_move_report(self):
        report_data = self.get_moves()
        return self.env.ref('internal_stock_transfer_app.internal_stock_move_report').with_context(
            landscape=True).report_action(
            None,
            data=report_data)

    def action_print_stock_move_csv(self):
        report_data = self.get_moves()
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
        content = output.getvalue().encode('utf-8')
        filename = 'InternalStockMove.csv'
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
