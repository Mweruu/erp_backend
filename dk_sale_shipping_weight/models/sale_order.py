from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_default_weight_uom(self):
        return self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    shipping_weight = fields.Float('Shipping Weight', compute='_calculate_shipping_weight', readonly=True)

    weight_uom_name = fields.Char(string='Weight unit of measure label', default=_get_default_weight_uom)

    @api.depends('order_line.product_template_id', 'order_line.product_uom_qty')
    def _calculate_shipping_weight(self):
        total_weight = 0
        for order in self:
            for orderline in order.order_line:
                total_weight = orderline.shipping_weight
            self.shipping_weight = total_weight


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    shipping_weight = fields.Float('Shipping Weight', compute='_compute_shipping_weight')

    @api.depends('product_uom_qty', 'product_template_id')
    def _compute_shipping_weight(self):
        total_weight = 0
        for orderline in self:
            total_weight += orderline.product_id.weight * orderline.product_uom_qty
            self.shipping_weight = total_weight
