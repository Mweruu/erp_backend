from datetime import datetime
from odoo import api, fields, models
import base64
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ScheduledActions(models.Model):
    _inherit = "pos.config"
    email_to = fields.Char('Email', required=True, default='example@example.com')

    @api.model
    def _cron_send_reports(self):
        param_id = self.env.context.get('params', {}).get('id')
        ir_cron = self.env['ir.cron'].search([('id', '=', param_id)])
        email_to = ir_cron.email_to
        logger.debug(f"email sent to {email_to}")

        quantity_track_report = self.env['quantity.track.report'].create({})
        report = quantity_track_report.get_quantity_report_data()

        sales_price_differences = self.env['sales.price.differences'].create({})
        report2 = sales_price_differences.get_sales_price_difference_report_data()

        pos_order_report_refunds = self.env['pos.order.report.refunds'].create({})
        report3 = pos_order_report_refunds.get_refunds_report_data()

        pos_order_report_diffs = self.env['sale.order.report.diffs'].create({})
        report4 = pos_order_report_diffs.get_price_difference_report_data()

        base_price_report = self.env['base.price.report'].create({})
        report6 = base_price_report.get_base_price_report_data()

        product_discounts_report = self.env['product.discounts.report'].create({})
        report7 = product_discounts_report.get_product_discounts_report_data()

        purchase_order_report = self.env['purchase.order.report'].create({})
        report8 = purchase_order_report.get_purchase_report_data()

        pos_order_report_diffs = self.env['pos.order.report.diffs'].create({})
        report9 = pos_order_report_diffs.get_difference_report_data()

        gift_cards_report = self.env['gift.cards.report'].create({})
        report10 = gift_cards_report.get_gift_cards_report_data()

        retention_tax_report = self.env['retention.tax.report'].create({})
        report11 = retention_tax_report.get_retention_tax()

        journal_items_report = self.env['journal.items.report'].create({})
        report12 = journal_items_report.get_journals()

        sales_reports = self.env['sales.reports'].create({})
        report13 = sales_reports.get_sales_report_data()

        Order_refunds = self.env['pos.order.refunds'].create({})
        report14 = Order_refunds.get_refunded_orders_report_data()

        pdfs = [
            self.env.ref('pos_sale_report.quantity_track_report')._render(
                'pos_sale_report.quantity_track_report_template', report),
            self.env.ref('pos_sale_report.sales_price_difference_report')._render(
                'pos_sale_report.sales_price_difference_report_template', report2),
            self.env.ref('pos_sale_report.k_pos_refunds_transactions_report')._render(
                'pos_sale_report.k_pos_refunds_transactions_report_template', report3),
            self.env.ref('pos_sale_report.k_sale_orders_transactions_report')._render(
                'pos_sale_report.k_sale_orders_transactions_report_template', report4),
            self.env.ref('pos_sale_report.base_price_report')._render(
                'pos_sale_report.base_price_report_template', report6),
            self.env.ref('pos_sale_report.product_discounts_report')._render(
                'pos_sale_report.product_discounts_report_template', report7),
            self.env.ref('pos_sale_report.purchase_order_report')._render(
                'pos_sale_report.purchase_report_template', report8),
            self.env.ref('pos_sale_report.k_pos_orders_transactions_report')._render(
                'pos_sale_report.k_pos_orders_transactions_report_template', report9),
            self.env.ref('pos_sale_report.gift_cards_report')._render(
                'pos_sale_report.gift_cards_report_template', report10),
            self.env.ref('od_retention_tax.retention_tax_report')._render(
                'od_retention_tax.retention_tax_report_template', report11),
            self.env.ref('journal_items_report.journal_items_report')._render(
                'journal_items_report.journal_items_report_template', report12),
            self.env.ref('pos_sale_report.sales_report')._render(
                'pos_sale_report.sales_report_template', report13),
            self.env.ref('pos_sale_report.k_pos_refunded_orders_transactions_report')._render(
                'pos_sale_report.k_pos_refunded_orders_transactions_report_template', report14),

        ]
        templates = [
            self.env.ref('pos_sale_report.quantity_track_report_template').name,
            self.env.ref('pos_sale_report.sales_price_difference_report_template').name,
            self.env.ref('pos_sale_report.k_pos_refunds_transactions_report_template').name,
            self.env.ref('pos_sale_report.k_sale_orders_transactions_report_template').name,
            self.env.ref('pos_sale_report.base_price_report_template').name,
            self.env.ref('pos_sale_report.product_discounts_report_template').name,
            self.env.ref('pos_sale_report.purchase_report_template').name,
            self.env.ref('pos_sale_report.k_pos_orders_transactions_report_template').name,
            self.env.ref('pos_sale_report.gift_cards_report_template').name,
            self.env.ref('od_retention_tax.retention_tax_report_template').name,
            self.env.ref('journal_items_report.journal_items_report_template').name,
            self.env.ref('pos_sale_report.sales_report_template').name,
            self.env.ref('pos_sale_report.k_pos_refunded_orders_transactions_report_template').name

        ]
        names = [
            self.env.ref('pos_sale_report.quantity_track_report').name,
            self.env.ref('pos_sale_report.sales_price_difference_report').name,
            self.env.ref('pos_sale_report.k_pos_refunds_transactions_report').name,
            self.env.ref('pos_sale_report.k_sale_orders_transactions_report').name,
            self.env.ref('pos_sale_report.base_price_report').name,
            self.env.ref('pos_sale_report.product_discounts_report').name,
            self.env.ref('pos_sale_report.purchase_order_report').name,
            self.env.ref('pos_sale_report.k_pos_orders_transactions_report').name,
            self.env.ref('pos_sale_report.gift_cards_report').name,
            self.env.ref('od_retention_tax.retention_tax_report').name,
            self.env.ref('journal_items_report.journal_items_report').name,
            self.env.ref('pos_sale_report.sales_report').name,
            self.env.ref('pos_sale_report.k_pos_refunded_orders_transactions_report').name,

        ]

        for pdf, template, name in zip(pdfs, templates, names):
            data = pdf[0]
            values = {
                'subject': '{} for {}'.format(name, datetime.today().strftime('%d-%m-%Y')),
                'body_html': name,
                'email_to': email_to,
            }
            mail_values = {
                'subject': values['subject'],
                'body_html': values['body_html'],
                'email_to': values['email_to'],
                'attachment_ids': [(0, 0, {
                    'name': name,
                    'datas': base64.encodebytes(data),
                    'mimetype': 'application/pdf'
                })],
            }

            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send()


class ScheduledAction(models.Model):
    _inherit = "ir.cron"

    email_to = fields.Char('Email', required=True, default='example@example.com')
