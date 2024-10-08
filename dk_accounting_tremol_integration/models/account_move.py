import logging
from odoo import models, fields, _
import re

from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_ke_validate_move(self):
        """ Returns list of errors related to misconfigurations per move

        Find misconfigurations on the move, the lines of the move, and the
        taxes on those lines that would result in rejection by the KRA.
        """
        errors = []
        for move in self:
            move_errors = []
            if move.country_code != 'KE':
                move_errors.append(
                    _("This invoice is not a Kenyan invoice and therefore can not be sent to the device."))

            if move.company_id.currency_id != self.env.ref('base.KES'):
                move_errors.append(
                    _("This invoice's company currency is not in Kenyan Shillings, conversion to KES is not possible."))

            if move.state != 'posted':
                move_errors.append(_("This invoice/credit note has not been posted. Please confirm it to continue."))

            if move.move_type not in ('out_refund', 'out_invoice'):
                move_errors.append(_("The document being sent should be an invoice or credit note."))

            if any([move.l10n_ke_cu_invoice_number, move.l10n_ke_cu_serial_number, move.l10n_ke_cu_qrcode,
                    move.l10n_ke_cu_datetime]):
                move_errors.append(
                    _("The document already has details related to the fiscal device. Please make sure that the invoice has not already been sent."))

            # The credit note should refer to the control unit number (receipt number) of the original
            # invoice to which it relates.
            if move.move_type == 'out_refund' and not move.reversed_entry_id.l10n_ke_cu_invoice_number:
                move_errors.append(
                    _("This credit note must reference the previous invoice, and this previous invoice must have already been submitted."))

            for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                if line.tax_ids.amount_type == 'group':
                    vat_taxes = line.tax_ids.children_tax_ids.filtered(lambda tax: tax.amount in (16, 8, 0))
                    if not vat_taxes or len(vat_taxes) > 1:
                        move_errors.append(_("On line %s, you must select one and only one VAT tax.", line.name))
                    else:
                        if vat_taxes[0].amount == 0 and not (
                                line.product_id and line.product_id.l10n_ke_hsn_code and line.product_id.l10n_ke_hsn_name):
                            move_errors.append(
                                _("On line %s, a product with a HS Code and HS Name must be selected, since the tax is 0%% or exempt.",
                                  line.name))
                else:
                    vat_taxes = line.tax_ids.filtered(lambda tax: tax.amount in (16, 8, 0))
                    if not vat_taxes or len(vat_taxes) > 1:
                        move_errors.append(_("On line %s, you must select one and only one VAT tax.", line.name))
                    else:
                        if vat_taxes[0].amount == 0 and not (
                                line.product_id and line.product_id.l10n_ke_hsn_code and line.product_id.l10n_ke_hsn_name):
                            move_errors.append(
                                _("On line %s, a product with a HS Code and HS Name must be selected, since the tax is 0%% or exempt.",
                                  line.name))

            if move_errors:
                errors.append((move.name, move_errors))

        return errors

    def _l10n_ke_cu_lines_messages(self):
        """ Serialise the data of each line on the invoice

        This function transforms the lines in order to handle the differences
        between the KRA expected data and the lines in odoo.

        If a discount line (as a negative line) has been added to the invoice
        lines, find a suitable line/lines to distribute the discount accross

        :returns: List of byte-strings representing each command <CMD> and the
                  <DATA> of the line, which will be sent to the fiscal device
                  in order to add a line to the opened invoice.
        """
        def is_discount_line(line):
            return line.price_subtotal < 0.0

        def is_candidate(discount_line, other_line):
            """ If the of one line match those of the discount line, the discount can be distributed accross that line """
            discount_taxes = discount_line.tax_ids.flatten_taxes_hierarchy()
            other_line_taxes = other_line.tax_ids.flatten_taxes_hierarchy()
            return set(discount_taxes.ids) == set(other_line_taxes.ids)

        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product' and l.quantity and l.price_total)
        # The device expects all monetary values in Kenyan Shillings
        if self.currency_id == self.company_id.currency_id:
            currency_rate = 1
        # In the case of a refund, use the currency rate of the original invoice
        elif self.move_type == 'out_refund' and self.reversed_entry_id:
            currency_rate = abs(self.reversed_entry_id.amount_total_signed / self.reversed_entry_id.amount_total)
        else:
            currency_rate = abs(self.amount_total_signed / self.amount_total)

        discount_dict = {line.id: line.discount for line in lines if line.price_total > 0}
        for line in lines:
            if not is_discount_line(line):
                continue
            # Search for non-discount lines
            candidate_vals_list = [l for l in lines if not is_discount_line(l) and is_candidate(l, line)]
            candidate_vals_list = sorted(candidate_vals_list, key=lambda x: x.price_unit * x.quantity, reverse=True)
            line_to_discount = abs(line.price_unit * line.quantity)
            for candidate in candidate_vals_list:
                still_to_discount = abs(candidate.price_unit * candidate.quantity * (100.0 - discount_dict[candidate.id]) / 100.0)
                if line_to_discount >= still_to_discount:
                    discount_dict[candidate.id] = 100.0
                    line_to_discount -= still_to_discount
                else:
                    rest_to_discount = abs((line_to_discount / (candidate.price_unit * candidate.quantity)) * 100.0)
                    discount_dict[candidate.id] += rest_to_discount
                    break

        vat_class = {16.0: 'A', 8.0: 'B'}
        msgs = []
        tax_details = self._prepare_invoice_aggregated_taxes()
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product' and l.quantity and l.price_total > 0 and not discount_dict.get(l.id) >= 100):
            # Here we use the original discount of the line, since it the distributed discount has not been applied in the price_total
            price_total = 0
            percentage = 0
            for tax in tax_details['tax_details_per_record'][line]['tax_details']:
                if tax['tax'].amount in (16, 8, 0): # This should only occur once
                    line_tax_details = tax_details['tax_details_per_record'][line]['tax_details'][tax]
                    price_total = abs(line_tax_details['base_amount_currency']) + abs(line_tax_details['tax_amount_currency'])
                    percentage = tax['tax'].amount

            price = round(price_total / abs(line.quantity) * 100 / (100 - line.discount), 2) * currency_rate
            price = ('%.5f' % price).rstrip('0').rstrip('.')

            # Letter to classify tax, 0% taxes are handled conditionally, as the tax can be zero-rated or exempt
            letter = ''
            if percentage in vat_class:
                letter = vat_class[percentage]
            else:
                report_line_ids = line.tax_ids.invoice_repartition_line_ids.tag_ids._get_related_tax_report_expressions().report_line_id.ids
                try:
                    exempt_report_line = self.env.ref('l10n_ke.tax_report_line_exempt_sales')
                except ValueError:
                    raise UserError(_("Tax exempt report line cannot be found, please update the l10n_ke module."))
                letter = 'E' if exempt_report_line.id in report_line_ids else 'C'

            uom = line.product_uom_id and line.product_uom_id.name or ''
            hscode = re.sub('[^0-9.]+', '', line.product_id.l10n_ke_hsn_code)[:10].ljust(10).encode('cp1251') if letter not in ('A', 'B') else b''.ljust(10)
            hsname = self._l10n_ke_fmt(line.product_id.l10n_ke_hsn_name, 20) if letter not in ('A', 'B') else b''.ljust(20)
            full_product_name = [
                move.company_id.is_product_name if move.company_id.is_set_product_name and (move.company_id.is_product_name != None and move.company_id.is_product_name != False and move.company_id.is_product_name != '')
                else line.name
                for move in self
            ]
            line_data = b';'.join([
                self._l10n_ke_fmt(full_product_name, 36),               # 36 symbols for the article's name
                self._l10n_ke_fmt(letter, 1),                   # 1 symbol for article's vat class ('A', 'B', 'C', 'D', or 'E')
                price[:15].encode('cp1251'),                    # 1 to 15 symbols for article's price with up to 5 digits after decimal point
                self._l10n_ke_fmt(uom, 3),                      # 3 symbols for unit of measure
                hscode,                                         # 10 symbols for HS code in the format xxxx.xx.xx (can be empty)
                hsname,                                         # 20 symbols for the HS name (can be empty)
                str(percentage).encode('cp1251')[:5]            # up to 5 symbols for vat rate
            ])
            # 1 to 10 symbols for quantity
            line_data += b'*' + str(abs(line.quantity)).encode('cp1251')[:10]
            if discount_dict.get(line.id):
                # 1 to 7 symbols for percentage of discount/addition
                discount_sign = b'-' if discount_dict[line.id] > 0 else b'+'
                discount = discount_sign + str(abs(discount_dict[line.id])).encode('cp1251')[:6]
                line_data += b',' + discount + b'%'

            # Command: Sale of article (0x31)
            msgs += [b'\x31' + line_data]
        return msgs
