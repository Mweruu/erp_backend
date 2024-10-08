from odoo import models, fields, api, _
import pytz
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    customer_number = fields.Char(string='Customer Number')
    delivered = fields.Boolean(string='Delivered')
    delay_picking = fields.Boolean(string='Delay Picking')
    color = fields.Selection([('blue', 'Blue'), ('yellow', 'Yellow')], string='Colour')
    reprinted = fields.Boolean(string='Reprinted')
    vat_number = fields.Char(string='PIN Number', default='')

    def _order_fields(self, ui_order):
        """ Prepare dictionary for create method """
        fields = ['customer_number', 'delivered', 'delay_picking', 'color', 'reprinted']
        result = super(PosOrder, self)._order_fields(ui_order)
        for field in fields:
            result[field] = ui_order[field] if field in ui_order else False
            result["vat_number"] = ui_order['vat_number'] if not ui_order['partner_id'] else False
        return result

    def confirm_coupon_programs(self, coupon_data):
        res = super(PosOrder, self).confirm_coupon_programs(coupon_data)
        for report_entry in res['coupon_report'].items():
            gift_card = self.env['loyalty.card'].search_read([('id', 'in', report_entry[1])])
            res['new_coupon_info'].append({
                'giftcard_info': gift_card
            })
        return res

    def _prepare_done_order_line_for_pos(self, order_line):
        pattern = re.compile(r'\[.*?\]')
        name = re.sub(pattern, '', order_line.product_id.display_name)
        return {
            "product_id": order_line.product_id.id,
            "qty": order_line.qty,
            "price_unit": order_line.price_unit,
            "discount": order_line.discount,
            "customer_note": order_line.customer_note,
            "pack_lot_names": order_line.pack_lot_ids.mapped("lot_name"),
            "name": name,
            "subtotal": order_line.price_subtotal,
            "subtotalInc": order_line.price_subtotal_incl,
            "uom": order_line.product_id.uom_id.name,
            "price_unit_discounted": order_line.price_unit - order_line.discount,
            "price": (
                    order_line.price_subtotal_incl / order_line.qty) if order_line.qty != 0 else order_line.price_unit,
        }

    def _prepare_coupon_info(self, coupon):
        return {
            "giftcard_info": coupon.program_id.name if coupon.program_id.program_type == 'gift_card' else False,
            "program_name": coupon.program_id.name,
            "expiration_date": coupon.expiration_date,
            "code": coupon.code,
            "points": coupon.points
        }

    def _prepare_loyalty_stats(self, program_type):
        program = [p.name for p in program_type.program_id]
        points = sum(prog_type.points for prog_type in program_type)
        return {
            "program": program,
            "points": round(points, 2),
        }

    def _prepare_done_order_payment_for_pos(self, payment_line):
        return {
            "name": payment_line.payment_method_id.name,
            "amount": payment_line.amount,
            "return": payment_line.name
        }

    def _get_tax_details(self, tax_details, order_line):
        tax_amounts = {}
        total_tax = 0
        for line in order_line:
            for tax_id in line.tax_ids_after_fiscal_position:
                if tax_id.id not in tax_amounts:
                    tax_amounts[tax_id.id] = []
                tax_amount = line.price_subtotal * (tax_id.amount / 100)
                tax_amounts[tax_id.id].append(tax_amount)
        sums = {key: sum(values) for key, values in tax_amounts.items()}
        for key, total in sums.items():
            if tax_details.id == key:
                total_tax = total
        return {
            "amount": total_tax,
            "name": tax_details.name,
            "tax_amount": tax_details.amount,
        }

    def getOrderDetails(self, order):
        # datetime object containing current date and time UTC/GMT +3 = Etc/GMT-3
        local_tz = pytz.timezone('Etc/GMT-3')
        local_create_date = datetime.now().astimezone(local_tz)
        # dd/mm/YY H:M:S
        validation_date = local_create_date.strftime("%m/%d/%Y %H:%M:%S")
        order_lines = []
        payment_lines = []
        new_coupon_info = []
        loyaltyStats = []
        sum_discount = 0
        tax_details = []
        for order_line in order.lines:
            order_line = self._prepare_done_order_line_for_pos(order_line)
            order_lines.append(order_line)
        for order_line in order.lines:
            if order_line.discount > 0:
                normal_price = order_line.qty * order_line.price_unit
                normal_price = normal_price + (normal_price / 100 * order_line.tax_ids.amount)
                sum_discount += normal_price - order_line.price_subtotal_incl
        for payment_line in order.payment_ids:
            payment_line = self._prepare_done_order_payment_for_pos(
                payment_line)
            payment_lines.append(payment_line)
        for tax_detail in order.lines.tax_ids:
            tax_detail = self._get_tax_details(
                tax_detail, order.lines)
            tax_details.append(tax_detail)

        cu_datetime = getattr(order, 'l10n_ke_cu_datetime', False)
        if cu_datetime:
            local_create_cu_date = cu_datetime.astimezone(local_tz)
            l10n_ke_cu_datetime = local_create_cu_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            l10n_ke_cu_datetime = False

        programs = self.env['loyalty.program'].search([('program_type', 'in', ['next_order_coupons', 'gift_card'])])
        for program in programs:
            coupons = self.env['loyalty.card'].search(
                [('program_id', '=', program.id), ('source_pos_order_id', '=', order.id)])
            for coupon in coupons:
                coupon_info = self._prepare_coupon_info(coupon)
                new_coupon_info.append(coupon_info)
        if order.partner_id:
            program = self.env['loyalty.program'].search([('program_type', '=', 'loyalty',)])
            program_type = self.env['loyalty.card'].search([('program_id', 'in', program.ids),
                                                            ('partner_id', '=', order.partner_id.id)])
            loyalty_stats = self._prepare_loyalty_stats(program_type)
            loyaltyStats.append(loyalty_stats)

        res = {
            "id": order.id,
            "creation_date": order.date_order,
            "validation_date": validation_date,
            "pos_reference": order.pos_reference,
            "name": order.name,
            "partners": order.partner_id.name,
            "partner_email": order.partner_id.email,
            "fiscal_position": order.fiscal_position_id.id,
            "orderlines": order_lines,
            "new_coupon_info": new_coupon_info,
            "loyaltyStats": loyaltyStats,
            "paymentlines": payment_lines,
            "to_invoice": bool(order.to_invoice),
            "receipt_footer": order.config_id.receipt_footer,
            "receipt_header": order.config_id.receipt_header,
            "cashier": order.user_id.name,
            "if_tax": (True if order.amount_tax > 0 else False),
            "total_amount_wo_tax": (order.amount_total - order.amount_tax),
            "total": order.amount_total,
            "amount_tax": order.amount_tax,
            "customer_number": order.customer_number,
            "delay_picking": order.delay_picking,
            "total_discount": sum_discount,
            "change": order.amount_return,
            "manual_etr": getattr(order, 'manual_etr', True),
            'tax_details': tax_details,
            'l10n_ke_cu_datetime': getattr(order, 'l10n_ke_cu_datetime', False),
            'l10n_ke_cu_serial_number': getattr(order, 'l10n_ke_cu_serial_number', False),
            'l10n_ke_cu_invoice_number': getattr(order, 'l10n_ke_cu_invoice_number', False),
            'l10n_ke_cu_qrcode': getattr(order, 'l10n_ke_cu_qrcode', False),
            '_printed': False,
            'finalized': True,
            "company_details": {
                'name': order.company_id.name,
                'contact_address': order.company_id.partner_id.contact_address,
                'phone': order.company_id.phone,
                'vat_label': (order.company_id.vat if order.company_id.vat else False),
                'vat': order.company_id.vat,
                'email': order.company_id.email,
                'website': order.company_id.website,
                'logo': order.company_id.logo
            },
            "company": {
                'name': order.company_id.name,
                'contact_address': order.company_id.partner_id.contact_address,
                'phone': order.company_id.phone,
                'vat_label': (order.company_id.vat if order.company_id.vat else False),
                'email': order.company_id.email,
                'website': order.company_id.website,
                'logo': order.company_id.logo
            }
        }
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    reserved_qty = fields.Float(
        compute='_compute_reserved_qty', string='Reserved Quantity')
    actual_qty = fields.Float(
        compute='_compute_actual_qty', string='Actual Quantity')

    # Compute Reserved Quantity by sum of orders from POS with Delayed Picking
    def _compute_reserved_qty(self):
        for product in self:
            self.env.cr.execute("SELECT COALESCE(sum(l.qty), 0) FROM pos_order o \
                        JOIN pos_order_line l on o.id = l.order_id \
                        JOIN product_product p on p.id = l.product_id \
                        WHERE o.delay_picking = true and o.delivered = false and p.product_tmpl_id = %s;",
                                (product.id,))
            product.reserved_qty = self.env.cr.fetchall()[0][0]

    # Compute Actual Quantity by formula i.e: Actual Quantity = Quantity in Hands - Reserved Quantity
    def _compute_actual_qty(self):
        for product in self:
            product.actual_qty = product.qty_available - product.reserved_qty
