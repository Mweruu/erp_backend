from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError


class RefundModel(models.Model):
    _inherit = 'pos.order'

    def refund_and_payment(self):
        refund_orders = self.env['pos.order']
        for order in self:
            current_session = order.session_id.config_id.current_session_id
            if not current_session:
                raise UserError(_('To return product(s), you need to open a session in the POS %s',
                                  order.session_id.config_id.display_name))
            refund_order = order.copy(
                order._prepare_refund_values(current_session)
            )
            for line in order.lines:
                PosOrderLineLot = self.env['pos.pack.operation.lot']
                for pack_lot in line.pack_lot_ids:
                    PosOrderLineLot += pack_lot.copy()
                line.copy(line._prepare_refund_data(refund_order, PosOrderLineLot))
            refund_orders |= refund_order

        action = self.env.ref('point_of_sale.action_pos_payment').read()[0]
        action['context'] = {
            'active_id': refund_orders.ids[0],
            'default_amount': refund_orders.amount_total,
            'default_journal_id': refund_orders.session_id.config_id.journal_id.id,
        }
        return action
