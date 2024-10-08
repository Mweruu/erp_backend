from datetime import datetime
import base64
from odoo import models, fields, api, _
import logging
import csv
import io
import pytz
from itertools import chain
from collections import defaultdict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SummaryRaxReport(models.Model):
    _name = "summary.tax.report"
    _description = "Summary of the total tax amount sent to TIMS"

    date = fields.Date(default=datetime.now())

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def get_summary_tax_report_data(self):
        pos_data = []
        invoice_data = []
        total_pos = 0
        total_invoices = 0
        serial_data = []
        serial_numbers = self.env['pos.order'].search([('create_date', '>=', self.date_from),
                                                       ('create_date', '<=', self.date_to)]).mapped(
            'l10n_ke_cu_serial_number')
        unique_serial_numbers = list(set(serial_numbers))
        invoice_serial_numbers = self.env['account.move'].search([('create_date', '>=', self.date_from),
                                                                  ('create_date', '<=', self.date_to)]).mapped(
            'l10n_ke_cu_serial_number')
        unique_invoice_serial_numbers = list(set(invoice_serial_numbers))

        for serial_number in unique_serial_numbers:
            pos_taxes = self.env['pos.order'].search([('create_date', '>=', self.date_from),
                                                      ('create_date', '<=', self.date_to),
                                                      # ('manual_etr', '=', False),
                                                      ('l10n_ke_cu_serial_number', '=', serial_number)
                                                      ])
            total_pos_for_serial = sum(tax.amount_tax for tax in pos_taxes)
            total_pos += total_pos_for_serial
            pos_data.append({
                'serial_number': serial_number if serial_number else 'Other Devices',
                'total_pos_for_serial': total_pos_for_serial
            })
        for inv_serial_number in unique_invoice_serial_numbers:
            taxed_invoices = self.env['account.move'].search([('create_date', '>=', self.date_from),
                                                              ('create_date', '<=', self.date_to),
                                                              ('move_type', 'in', ['out_invoice', 'out_refund']),
                                                              ('l10n_ke_cu_serial_number', '=', inv_serial_number)
                                                              ])
            wht_tax_group = self.env['account.tax.group'].search([('name', '=', 'Withholding Tax')])
            tax_ids = [tax.id for tax in taxed_invoices]
            taxed_invoices_lines = self.env['account.move.line'].search([('create_date', '>=', self.date_from),
                                                                         ('create_date', '<=', self.date_to),
                                                                         ('move_id', 'in', tax_ids),
                                                                         ('tax_group_id', '!=', wht_tax_group.id),
                                                                         ('tax_group_id', '!=', False)
                                                                         ])
            total_credit = sum(tax.debit for tax in taxed_invoices_lines)
            total_debit = sum(tax.credit for tax in taxed_invoices_lines)
            total_invoice_for_serial = total_debit - total_credit
            total_invoices += total_invoice_for_serial
            invoice_data.append({
                'serial_number': inv_serial_number if inv_serial_number else 'Other Devices',
                'sales_credit': total_credit,
                'sales_debit': total_debit,
                'total_invoice_for_serial': total_invoice_for_serial
            })

        sum_by_serial_number = defaultdict(float)
        for entry in chain(invoice_data, pos_data):
            serial_number = entry['serial_number']
            if 'total_invoice_for_serial' in entry:
                sum_by_serial_number[serial_number] += entry['total_invoice_for_serial']
            elif 'total_pos_for_serial' in entry:
                sum_by_serial_number[serial_number] += entry['total_pos_for_serial']
        for serial_number, total in sum_by_serial_number.items():
            print(f"Serial Number: {serial_number}, Total: {total}")
            serial_data.append({
                'total_tax': total,
                'serial_number': serial_number
            })

        data = {
            'records': pos_data,
            'inv_records': invoice_data,
            'self': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'total_pos': round(total_pos, 2),
            'total_invoices': round(total_invoices, 2),
            'total': total_pos + total_invoices,
            'serial_data': serial_data,

        }
        return data

    def action_print_summary_tax_report(self):
        report_data = self.get_summary_tax_report_data()
        return self.env.ref('dk_pos_tremol_integration.summary_tax_report').with_context(landscape=True). \
            report_action(None, data=report_data)
