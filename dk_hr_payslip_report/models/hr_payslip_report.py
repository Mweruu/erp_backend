import base64
import csv
import io
import logging
from datetime import datetime

from odoo import models, fields, api

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class HrPayslipReport(models.Model):
    _name = "hr.payslip.report"
    _description = "payslip report"

    @api.model
    def _default_payslip_batches(self):
        query = """
            select hpr."name" as id, hpr."name"  as name from hr_payslip_run as hpr
        """
        self.env.cr.execute(query, )
        name = self.env.cr.fetchall()
        return name

    payslip_batches = fields.Selection(selection=_default_payslip_batches, string='Payslip batches', required=True)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_hr_payslip_report_data(self):
        data = []
        query = """ 
            select DATE(hpr.create_date) as date, hp."name" as name, hp."number" as number, he."name" as user, rpb.acc_number as bank_account,  hpl.amount as amount from hr_payslip_run as hpr
                JOIN hr_payslip as hp ON hp.payslip_run_id = hpr.id
                JOIN hr_employee as he ON he.id  = hp.employee_id 
                LEFT JOIN res_partner_bank as rpb ON rpb.id  = he.bank_account_id 
                join hr_payslip_line as hpl on hpl.slip_id = hp.id
            where hpr."name"  = %s
        """

        self.env.cr.execute(query, (self.payslip_batches,))
        order_lines = self.env.cr.fetchall()
        for order_line in order_lines:
            data.append({
                'slip_number': order_line[2],
                'user': order_line[3],
                'bank_account': order_line[4],
                'amount': order_line[5],
            })

        # sorted_data = sorted(data, key=lambda tot: tot['tot'])
        data = {
            'records': data,
            'self': self.read()[0],
            'payslip_batches': self.payslip_batches,
            'date_to': self.date_to,
            'date_from': self.date_from
        }
        return data

    def action_print_hr_payslip_report(self):
        report_data = self.get_hr_payslip_report_data()
        return self.env.ref('dk_hr_payslip_report.hr_payslip_report').with_context(
            landscape=True).report_action(self, data=report_data)

    def action_print_hr_payslip_report_csv(self):
        report_data = self.get_hr_payslip_report_data()
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
        # grand_total_row = [''] * (len(header_row) - 1) + [report_data['grand_total']]  # Fill empty columns with ''
        # writer.writerow(grand_total_row)
        content = output.getvalue().encode('utf-8')
        filename = 'PayrollReport.csv'
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
