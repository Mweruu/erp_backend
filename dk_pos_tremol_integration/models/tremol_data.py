from datetime import datetime
import base64
from odoo import models, fields, api
import logging
import csv
import io
import os
import json

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
    folder_path = fields.Char( 'Folder', required=True)

    def sum_total_tax_by_dates(self, folder_path, dates):
        """
        Sums the TotalTaxAmount from JSON files in a folder based on specific dates.

        Args:
        - folder_path (str): The path to the folder containing the JSON files.
        - dates (list of str): The list of dates to filter invoices, in "YYYY-MM-DD" format.

        Returns:
        - total_tax (float): The sum of the TotalTaxAmount for the specified dates.
        """
        total_tax = 0.0
        total_amount = 0.0

        # Loop through the files in the folder
        try:
            for filename in os.listdir(folder_path):
                # if filename.endswith(".json"):
                if filename:
                    file_path = os.path.join(folder_path, filename)
                    # Open and load the JSON file
                    if os.path.isfile(file_path):
                        with open(file_path, 'r') as file:
                            try:
                                data = json.load(file)
                                # Access the list of invoices in the JSON structure
                                invoices = data["REPORT"]["DATA"]["INVOICES"]

                                # Loop through each invoice in the file
                                for invoice in invoices:
                                    # Extract the invoice date and convert it to a date object
                                    invoice_date_str = invoice["InvoiceDate"].split("T")[0]
                                    invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d").date()
                                    # If the invoice date is in the specified dates, add the TotalTaxAmount
                                    start_date = min(dates)
                                    end_date = max(dates)
                                    if start_date <= invoice_date <= end_date:
                                        total_invoice_amount = float(invoice["TotalInvoiceAmount"])
                                        total_tax_amount = float(invoice["TotalTaxAmount"])
                                        if invoice["InvoiceCategory"] == "Tax Invoice":
                                            total_amount += total_invoice_amount
                                            total_tax += total_tax_amount
                                        elif invoice["InvoiceCategory"] == "Credit Note":
                                            total_amount -= total_invoice_amount
                                            total_tax -= total_tax_amount
                            except json.JSONDecodeError:
                                logger.warning(f"Error reading JSON file: {file_path}")
                            except KeyError:
                                logger.warning(f"Unexpected JSON structure in file: {file_path}")
                            except UnicodeDecodeError:
                                logger.warning(f"The path {folder_path}{filename} is not valid.")
                                break
                    else:
                        logger.warning(f"The path {folder_path}{filename} is not valid.")
                        break

        except FileNotFoundError:
            logger.warning(f"No such file or directory: {folder_path}")

        return [total_amount, total_tax]

    def get_tremol_data_report_data(self):
        data = []
        total = 0
        tremol_data = []
        tremol_data += [b'\x6D']

        # Example usage:
        # folder_path = "/home/dellserver/Documents/tremol/"
        folder_path = self.folder_path
        dates_to_filter = [self.date_from, self.date_to]  # List of dates you want to filter

        sum = self.sum_total_tax_by_dates(folder_path, dates_to_filter)
        print(f"Total Tax Amount for specified dates: {sum[0]:.2f}, {sum[1]:.2f}")
        data.append({
            'Total Invoice Amount': round(sum[0], 2),
            'Total Tax Amount': round(sum[1], 2)
        })
        # for t_data in tremol_data:
        #     print(t_data[0])
        #     data.append({
        #         'Datetime':t_data[0]
        #     })

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
        if not report_data['records']:
            logger.info(f"No data")
            return {
                'warning': {
                    'title': 'No Data',
                    'message': 'There is no data to export.',
                },
            }
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
