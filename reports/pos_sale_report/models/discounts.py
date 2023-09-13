from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Discounts(models.Model):
    _inherit = "product.template"

    minimum_allowed_price = fields.Float(string='Minimum Allowed Price', digits='Product Price',
                                         default=0.0)
    list_base_price = fields.Float(string='Sale Base Price', digits='Product Price', required=True, default=0.0)
    discounts_ids = fields.One2many('product.discounts', 'discount_id', string='Discounts')

    @api.model
    def _get_global_discount_value(self):
        global_discount_value = self.env['ir.config_parameter'].sudo().get_param(
            'pos_sale_report.global_discount_value')
        return float(global_discount_value) if global_discount_value else 0.0

    @api.depends('list_base_price')
    def _compute_new_standard_price(self):
        global_discount = self._get_global_discount_value()
        amount = self.env['account.tax'].browse(1).amount
        for record in self:
            discount_percentage = float(global_discount) / 100
            rem = round(1 - discount_percentage, 2)
            tax = amount / 100
            taxes = round(1 + tax, 2)
            new_standard_price = round(record.list_base_price * rem * taxes, 2)
            logger.debug(f"new Standard Price:{new_standard_price},taxes:{taxes},amount:{amount}, tax:{tax},rem:{rem},discount_percentage:{discount_percentage}")
            record.new_standard_price = new_standard_price

    new_standard_price = fields.Float(string='Cost after discount', compute='_compute_new_standard_price', default=0.0)

    def get_global_disc(self):
        global_discount_value = self._get_global_discount_value()
        for record in self:
            record.global_discount_value = global_discount_value

    global_discount_value = fields.Float(string='Global Discount (%)', compute='get_global_disc')

    def get_variance(self):
        for record in self:
            variance = record.list_price - record.new_standard_price
            record.variance = variance

    def get_percentage(self):
        for record in self:
            variance = record.list_price - record.new_standard_price
            logger.debug(
                f"variance:{variance}, list price:{record.list_price},new standard price{record.new_standard_price}")

            if record.list_price != 0:
                variance_percentage = (variance * 100) / record.list_price
                logger.debug(f"variance_percentage{variance_percentage}")
                record.variance_percentage = variance_percentage
            else:
                record.variance_percentage = 0
                logger.debug("list_price is 0, variance_percentage cannot be calculated")

    variance = fields.Float("Variance", compute='get_variance')
    variance_percentage = fields.Float("%", compute='get_percentage')
