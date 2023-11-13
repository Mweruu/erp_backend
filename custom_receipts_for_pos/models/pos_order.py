from odoo import models, fields, api, SUPERUSER_ID


class PosOrders(models.Model):
    _inherit = 'pos.order'

    def deliver(self):
        print(self.env.context)
        print(self.env.context['params']['id'])
        current_id = self.env.context['params']['id']

        ship_later_order = self.env['stock.picking'].search_read([('id', '=', current_id)])
        print(ship_later_order)
        if ship_later_order['state'] == 'done':
            return True
        else:
            return False

    @api.depends('delivered')
    def get_user(self):
        if SUPERUSER_ID == self._uid:
            self.check_user = True
        else:
            self.check_user = False

    check_field = fields.Boolean(string='Check', compute='get_user')

    customer_number = fields.Char(string='Customer Number')
    delivered = fields.Boolean(string='Delivered')
    delay_picking = fields.Boolean(string='Delay Picking')
    colour = fields.Char(string='Colour')

    def _order_fields(self, ui_order):
        """ Prepare dictionary for create method """
        result = super()._order_fields(ui_order)
        result['customer_number'] = ui_order.get('customer_number')
        return result


class ShipLaterOrders(models.Model):
    _inherit = 'pos.order'

    def get_ship_later_orders(self):
        for record in self:
            print(record)
