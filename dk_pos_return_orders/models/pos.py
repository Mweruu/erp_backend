from odoo import fields, models, api, _


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_is_show_all_orders = fields.Boolean(related='pos_config_id.is_show_all_orders', readonly=False, store=True)
    pos_max_day_refund = fields.Integer(related='pos_config_id.max_day_refund', readonly=False, store=True)
    pos_is_enabled_refund = fields.Boolean(related='pos_config_id.is_enabled_refund', readonly=False, store=True)
    pos_is_enabled_invoice = fields.Boolean(related='pos_config_id.is_enabled_invoice', readonly=False, store=True)
    pos_is_enabled_print_on_refund = fields.Boolean(related='pos_config_id.is_enabled_print_on_refund', readonly=False,
                                                    store=True)


class POSConfig(models.Model):
    _inherit = 'pos.config'

    is_show_all_orders = fields.Boolean(string="Is Show All Orders On Refund")
    all_config_id = fields.Char(compute="_get_all_configs")
    max_day_refund = fields.Integer(string="Set Max Days Of Return/Refund Qty")
    is_enabled_refund = fields.Boolean(string="Is Enabled Refund Qty")
    is_enabled_invoice = fields.Boolean(string="Is Enabled Invoice")
    is_enabled_print_on_refund = fields.Boolean(string="Is Enabled Print Receipt onRefund")

    def _get_all_configs(self):
        for config in self:
            # Search for pos.orders related to the current company
            configs = self.env['pos.config'].search([('company_id', '=', config.company_id.id)])
            config.all_config_id = configs.ids


class PosOrderInherit(models.Model):
    _inherit = 'pos.order'

    pos_order_date = fields.Date('Oder Date', compute='get_order_date')

    def get_order_date(self):
        for order in self:
            order.pos_order_date = order.date_order.date()
