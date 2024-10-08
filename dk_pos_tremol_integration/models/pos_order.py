from odoo import fields, models, _, api
import re
import json
from datetime import datetime

from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    manual_etr = fields.Boolean(string="Manual ETR")
    l10n_ke_cu_datetime = fields.Datetime(string='CU Signing Date and Time', copy=False)
    l10n_ke_cu_serial_number = fields.Char(string='CU Serial Number', copy=False)
    l10n_ke_cu_invoice_number = fields.Char(string='CU Invoice Number', copy=False)
    l10n_ke_cu_qrcode = fields.Char(string='CU QR Code', copy=False)
    reversed_entry_id = fields.Many2one(
        comodel_name='pos.order',
        string="Reversal of",
        index='btree_not_null',
        readonly=True,
        copy=False,
        check_company=True,
    )
    reversal_order_id = fields.One2many('pos.order', 'reversed_entry_id')

    def _order_fields(self, ui_order):
        """ Prepare dictionary for create method """
        fields = ['l10n_ke_cu_qrcode', 'l10n_ke_cu_invoice_number', 'l10n_ke_cu_serial_number',
                  'reversed_entry_id', 'manual_etr']
        result = super(PosOrder, self)._order_fields(ui_order)
        if ui_order['l10n_ke_cu_datetime']:
            result["l10n_ke_cu_datetime"] = datetime.strptime(ui_order['l10n_ke_cu_datetime'], '%d-%m-%Y %H:%M')
        for field in fields:
            result[field] = ui_order[field] if field in ui_order else False
        return result

    def _prepare_refund_values(self, current_session):
        result = super(PosOrder, self)._prepare_refund_values(current_session)
        result['reversed_entry_id'] = self.id
        return result

    def _l10n_ke_fmt(self, string, length, ljust=True):
        """ Function for common formatting behaviour

        :param string: string to be formatted/encoded
        :param length: integer length to justify (if enabled), and then truncate the string to
        :param ljust:  boolean representing whether the string should be justified
        :returns:      byte-string justified/truncated, with all non-alphanumeric characters removed
        """
        if not string:
            string = ''
        return re.sub('[^A-Za-z0-9 ]+', '', str(string)).encode('cp1251').ljust(length if ljust else 0)[:length]

    # -------------------------------------------------------------------------
    # CHECKS
    # -------------------------------------------------------------------------

    def _l10n_ke_validate_order(self, orders):
        """ Returns list of errors related to misconfigurations per order
        Find misconfigurations on the order, the lines of the order, and the
        taxes on those lines that would result in rejection by the KRA.
        """
        errors = []
        taxableOrderLines = False

        def is_ewalletProgram(line):
            return 'eWalletGiftCardProgramId' in line[2] and line[2]['eWalletGiftCardProgramId'] is not None

        def is_rewardProgram(line):
            return 'is_reward_line' in line[2] and line[2]['is_reward_line'] is True

        def is_freeProduct(line):
            return 'price_subtotal_incl' in line[2] and line[2]['price_subtotal_incl'] < 0 < line[2]['qty']

        session = self.env['pos.session'].search([('id', '=', orders['pos_session_id'])])
        order_errors = []
        if orders['amount_tax'] == 0:
            order_errors.append(_("The total tax for this order is equal to 0. No ETR required"))
        if session.config_id.company_id.country_code != 'KE':
            order_errors.append(
                _("This order is not a Kenyan order and therefore can not be sent to the device."))

        if session.config_id.company_id.currency_id != self.env.ref('base.KES'):
            order_errors.append(
                _("This order's company currency is not in Kenyan Shillings, conversion to KES is not possible."))

        if any([orders['l10n_ke_cu_invoice_number'], orders['l10n_ke_cu_serial_number'], orders['l10n_ke_cu_qrcode'],
                orders['l10n_ke_cu_datetime']]):
            order_errors.append(
                _("The document already has details related to the fiscal device. Please make sure that the order has not already been sent."))

        # The credit note should refer to the control unit number (receipt number) of the original
        # order to which it relates.
        for orderline in orders['lines']:
            taxableOrderLines = True
            if is_ewalletProgram(orderline) or is_rewardProgram(orderline) or is_freeProduct(orderline):
                continue

            if orders['reversed_entry_id']:
                order = self.env['pos.order'].search([('id', '=', orders['reversed_entry_id'])])
                if orderline[2]['qty'] < 0 and not order.l10n_ke_cu_invoice_number:
                    order_errors.append(
                        _("This Refund must reference the previous order, and this previous order must have already been submitted."))
                    break

            account_tax = self.env['account.tax'].search([('id', 'in', orderline[2]['tax_ids'][0][2])])
            if not orderline[2]['tax_ids'] or len(orderline[2]['tax_ids']) > 1:
                order_errors.append(
                    _("On line %s, you must select one and only one tax.", orderline[2]['full_product_name']))

            else:
                product = self.env['product.product'].search([('id', '=', orderline[2]['product_id'])])
                if account_tax.amount == 0 and not (
                        product and product.l10n_ke_hsn_code and product.l10n_ke_hsn_name):
                    order_errors.append(
                        _("On line %s, a product with a HS Code and HS Name must be selected, since the tax is 0%% or exempt.",
                          orderline[2]['full_product_name']))
            if account_tax.amount not in (16, 8, 0):
                order_errors.append(
                    _("Tax '%s' is used, but only taxes of 16%%, 8%%, 0%% or Exempt can be sent. Please reconfigure or change the tax.",
                      account_tax.name))

        if order_errors:
            logger.warning(order_errors)
            errors.append((orders['name'], order_errors))

        if not taxableOrderLines:
            errors.append((orders['name'], ['No taxable lines in this order. No ETR Required']))

        return errors

    def _l10n_ke_cu_open_invoice_message(self, orders):
        """ Serialise the required fields for opening an order

        :returns: a list containing one byte-string representing the <CMD> and
                  <DATA> of the message sent to the fiscal device.
        """
        if orders['partner_id']:
            partner = self.env['res.partner'].search([('id', '=', orders['partner_id'])])
        else:
            partner = self.partner_id
        headquarter_address = (partner.commercial_partner_id.street or '') + (
                partner.commercial_partner_id.street2 or '')
        customer_address = (partner.street or '') + (partner.street2 or '')
        postcode_and_city = (partner.zip or '') + '' + (partner.city or '')
        vat = (
                partner.commercial_partner_id.vat or '').strip() if partner.commercial_partner_id.country_id.code == 'KE' else \
            orders['vat_number']
        invoice_elements = [
            b'1',  # Reserved - 1 symbol with value '1'
            b'     0',  # Reserved - 6 symbols with value ‘     0’
            b'0',  # Reserved - 1 symbol with value '0'
            b'1' if orders['amount_total'] > 0 else b'A',
            # 1 symbol with value '1' (new order), 'A' (credit note), or '@' (debit note)
            self._l10n_ke_fmt(partner.commercial_partner_id.name, 30),  # 30 symbols for Company name
            self._l10n_ke_fmt(vat, 14),  # 14 Symbols for the client PIN number
            self._l10n_ke_fmt(headquarter_address, 30),  # 30 Symbols for customer headquarters
            self._l10n_ke_fmt(customer_address, 30),  # 30 Symbols for the address
            self._l10n_ke_fmt(postcode_and_city, 30),  # 30 symbols for the customer post code and city
            self._l10n_ke_fmt('', 30),  # 30 symbols for the exemption number
        ]
        if orders['reversed_entry_id']:
            order = self.env['pos.order'].search([('id', '=', orders['reversed_entry_id'])])
            invoice_elements.append(
                self._l10n_ke_fmt(order.l10n_ke_cu_invoice_number, 19)),  # 19 symbols for related invoice number
        invoice_elements.append(re.sub('[^A-Za-z0-9 ]+', '', orders['name'])[-12:].ljust(12).encode(
            'cp1251'))  # 15 symbols for trader system invoice number
        # Command: Open fiscal record (0x30)
        return [b'\x30' + b';'.join(invoice_elements)]

        # -------------------------------------------------------------------------
        # POST COMMANDS / RECEIVE DATA   TremolG03Controller
        # -------------------------------------------------------------------------

    def _l10n_ke_cu_lines_messages(self, orders):
        """ Serialise the data of each line on the invoice
        This function transforms the lines in order to handle the differences
        between the KRA expected data and the lines in odoo.
        If a discount line (as a negative line) has been added to the invoice
        lines, find a suitable line/lines to distribute the discount accross
        :returns: List of byte-strings representing each command <CMD> and the
                  <DATA> of the line, which will be sent to the fiscal device
                  in order to add a line to the opened invoice.
        """
        session = self.env['pos.session'].search([('id', '=', orders['pos_session_id'])])

        def is_ewalletProgram(line):
            return 'eWalletGiftCardProgramId' in line[2] and line[2]['eWalletGiftCardProgramId'] is not None

        def is_rewardProgram(line):
            return 'is_reward_line' in line[2] and line[2]['is_reward_line'] is True

        def is_freeProduct(line):
            return 'price_subtotal_incl' in line[2] and line[2]['price_subtotal_incl'] < 0 < line[2]['qty']

        def is_discount_line(line):
            return line[2]['price_subtotal'] < 0.0

        def is_candidate(discount_line, other_line):
            discount_line = self.env['account.tax'].search([('id', 'in', discount_line[2]['tax_ids'][0][2])])
            other_line = self.env['account.tax'].search([('id', 'in', other_line[2]['tax_ids'][0][2])])
            """ If the of one line match those of the discount line, the discount can be distributed accross that line """
            discount_taxes = discount_line.flatten_taxes_hierarchy()
            other_line_taxes = other_line.flatten_taxes_hierarchy()
            return set(discount_taxes.ids) == set(other_line_taxes.ids)

        lines = orders['lines']
        # The device expects all monetary values in Kenyan Shillings
        if self.currency_id == session.config_id.company_id.currency_id:
            currency_rate = 1
        # In the case of a refund, use the currency rate of the original invoice
        elif orders['amount_total'] < 0 and orders['reversed_entry_id']:
            order = self.env['pos.order'].search([('id', '=', orders['reversed_entry_id'])])
            if order.amount_total != 0:  # Check if amount_total is not zero
                currency_rate = abs(order.amount_total / order.amount_total)
            else:
                # Handle the case where amount_total is zero
                currency_rate = 1  # Or any other appropriate value
        else:
            if orders['amount_total'] != 0:  # Check if amount_total is not zero
                currency_rate = abs(orders['amount_total'] / orders['amount_total'])
            else:
                # Handle the case where amount_total is zero
                currency_rate = 1  # Or any other appropriate value

        discount_dict = {line[2]['id']: line[2]['discount'] for line in lines if line[2]['price_unit'] > 0}
        for line in lines:
            if not is_discount_line(line):
                continue
            # Search for non-discount lines
            candidate_vals_list = [l for l in lines if not is_discount_line(l) and is_candidate(l, line)]
            candidate_vals_list = sorted(candidate_vals_list, key=lambda x: x[2]['price_unit'] * x[2]['qty'],
                                         reverse=True)
            line_to_discount = abs(line[2]['price_unit'] * line[2]['qty'])
            for candidate in candidate_vals_list:
                still_to_discount = abs(
                    candidate[2]['price_unit'] * candidate[2]['qty'] * (
                            100.0 - discount_dict[candidate[2]['id']]) / 100.0)
                if line_to_discount >= still_to_discount:
                    discount_dict[candidate[2]['id']] = 100.0
                    line_to_discount -= still_to_discount
                else:
                    rest_to_discount = abs(
                        (line_to_discount / (candidate[2]['price_unit'] * candidate[2]['qty'])) * 100.0)
                    discount_dict[candidate[2]['id']] += rest_to_discount
                    break

        vat_class = {16.0: 'A', 8.0: 'B'}
        msgs = []
        for line in lines:
            if is_ewalletProgram(line) or is_rewardProgram(line) or is_freeProduct(line):
                continue
            # Here we use the original discount of the line, since it the distributed discount has not been applied in the price_total
            price = round(
                abs(line[2]['price_subtotal_incl']) / abs(line[2]['qty']) * 100 / (100 - line[2]['discount']),
                2) * currency_rate
            price = ('%.5f' % price).rstrip('0').rstrip('.')
            account_tax = self.env['account.tax'].search([('id', 'in', line[2]['tax_ids'][0][2])])
            percentage = account_tax.amount

            # Letter to classify tax, 0% taxes are handled conditionally, as the tax can be zero-rated or exempt
            letter = ''
            if percentage in vat_class:
                letter = vat_class[percentage]
            else:
                report_line_ids = account_tax.invoice_repartition_line_ids.tag_ids._get_related_tax_report_expressions().report_line_id.ids
                try:
                    exempt_report_line = self.env.ref('l10n_ke.tax_report_line_exempt_sales')
                except ValueError:
                    raise UserError(_("Tax exempt report line cannot be found, please update the l10n_ke module."))
                letter = 'E' if exempt_report_line.id in report_line_ids else 'C'

            product = self.env['product.product'].search([('id', '=', line[2]['product_id'])])
            uom = product.product_tmpl_id.uom_id and product.product_tmpl_id.uom_id.name or ''
            hscode = re.sub('[^0-9.]+', '', product.product_tmpl_id.l10n_ke_hsn_code)[:10].ljust(10).encode(
                'cp1251') if letter not in ('A', 'B') else b''.ljust(10)
            hsname = self._l10n_ke_fmt(product.product_tmpl_id.l10n_ke_hsn_name, 20) if letter not in (
                'A', 'B') else b''.ljust(20)
            session = self.env['pos.session'].search([('id', '=', orders['pos_session_id'])])
            full_product_name = (session.config_id.is_product_name if session.config_id.is_set_product_name and (session.config_id.is_product_name != None and session.config_id.is_product_name != False and session.config_id.is_product_name != '')
                else line[2]['full_product_name'])
            line_data = b';'.join([
                self._l10n_ke_fmt(full_product_name, 36),  # 36 symbols for the article's name
                self._l10n_ke_fmt(letter, 1),  # 1 symbol for article's vat class ('A', 'B', 'C', 'D', or 'E')
                str(price)[:13].encode('cp1251'),  # 1 to 13 symbols for article's price
                self._l10n_ke_fmt(uom, 3),  # 3 symbols for unit of measure
                hscode,  # 10 symbols for HS code in the format xxxx.xx.xx (can be empty)
                hsname,  # 20 symbols for the HS name (can be empty)
                str(percentage).encode('cp1251')[:5]  # up to 5 symbols for vat rate
            ])
            line_data += b'*' + str(abs(line[2]['qty'])).encode('cp1251')[:10]
            if discount_dict.get(line[2]['id']):
                # 1 to 7 symbols for percentage of discount/addition
                discount_sign = b'-' if discount_dict[line[2]['id']] > 0 else b'+'
                discount = discount_sign + str(abs(discount_dict[line[2]['id']])).encode('cp1251')[:6]
                line_data += b',' + discount + b'%'

            # Command: Sale of article (0x31)
            msgs += [b'\x31' + line_data]
        return msgs

    def _l10n_ke_get_cu_messages(self, orders):
        """ Composes a list of all the command and data parts of the messages
            required for the fiscal device to open an invoice, add lines and
            subsequently close it.
        """
        msgs = self._l10n_ke_cu_open_invoice_message(orders)
        msgs += self._l10n_ke_cu_lines_messages(orders)
        # Command: Close fiscal reciept (0x38)
        msgs += [b'\x38']
        # Command: Read date and time (0x68)
        msgs += [b'\x68']
        logger.info("Formatted Message %s", json.dumps([msg.decode('cp1251') for msg in msgs]))
        return msgs

    @api.model
    def l10n_ke_action_cu_post(self, orders):
        """ Returns the client action descriptor dictionary for sending the
            invoice(s) to the fiscal device.
        """
        for orderline in orders['lines']:
            if orderline[2]['qty'] < 0:
                orders['reversed_entry_id'] = self.env['pos.order.line'].search(
                    [('id', '=', orderline[2]['refunded_orderline_id'])]).order_id.id
                break
        # Check the configuration of the invoice
        errors = self._l10n_ke_validate_order(orders)
        if errors:
            error_msg = ""
            for order, error_list in errors:
                error_list = '\n'.join(error_list)
                error_msg += _("Invalid order configuration on %s:\n%s\n\n", order, error_list)
            raise UserError(error_msg)
        session = self.env['pos.session'].search([('id', '=', orders['pos_session_id'])])
        return {
            'params': {
                'invoices': {
                    'messages': json.dumps([msg.decode('cp1251') for msg in self._l10n_ke_get_cu_messages(orders)]),
                    'proxy_address': session.config_id.l10n_pos_ke_cu_proxy_address,
                    'company_vat': session.config_id.company_id.vat,
                    'reversed_entry_id': orders['reversed_entry_id']
                }
            },
        }
