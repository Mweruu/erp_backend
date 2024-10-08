from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate_from_pos(self):
        order = self.env['pos.order'].search([('id', '=', self.pos_order_id.id)])
        for picking in self:
            for move in picking.move_ids.filtered(
                    lambda m: m.state not in ["done", "cancel"]
            ):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.reserved_uom_qty
            picking.with_context(skip_backorder=True, skip_sms=True).sudo().button_validate()

        self.env['pos.order'].browse(order.id).write({'delivered': True})
        PosOrder = self.env['pos.order']
        return_order_details = PosOrder.getOrderDetails(order)
        return {
            'response': 'success', 'title': 'Order Found',
            'body': 'Order with ID "' + str(order.name) + '" is ready to be picked up',
            'delayed_picking_order': return_order_details,
            'pos_order': order
        }
