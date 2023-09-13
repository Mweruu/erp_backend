from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ProductDiscounts(models.Model):
    _name = 'product.discounts'
    _description = 'Product Discounts'
    discount_id = fields.Many2one('product.template', string='Discount', readonly=True)
    name = fields.Char('Name', related='discount_id.name', index=True, required=True, translate=True)
    minimum_allowed_price = fields.Float(string='Minimum Allowed Price', digits='Product Price',
                                         default=0.0)

    @api.model
    def _get_global_discount_value(self):
        global_discount_value = self.env['ir.config_parameter'].sudo().get_param(
            'pos_sale_report.global_discount_value')
        return float(global_discount_value) if global_discount_value else 0.0

    def get_tax(self):
        amount = self.env['account.tax'].browse(1).amount
        return amount

    def get_variance(self):
        variance = self.list_price - self.new_standard_price
        return variance

    global_discount_value = fields.Float(string='Global Discount (%)', default='_get_global_discount_value')
    list_base_price = fields.Float(related='discount_id.list_base_price')
    standard_price = fields.Float(related='discount_id.standard_price')
    list_price = fields.Float(related='discount_id.list_price')
    new_standard_price = fields.Float(related='discount_id.new_standard_price', default=0.0)
    tax = fields.Float("Tax%", default='get_tax')
    variance = fields.Float("Variance", default='get_variance')
