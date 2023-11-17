from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate_from_pos(self):
        pickings = self.env['stock.move'].search([('picking_id', '=', self.id)])
        for picking in pickings:
            print(picking.quantity_done)
            picking.update({
                'quantity_done': picking.reserved_availability,
            })
            print(picking.quantity_done, picking, picking.reserved_availability)
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        if not self.env.context.get('skip_sanity_check', False):
            self._sanity_check()

        self.message_subscribe([self.env.user.partner_id.id])

        pickings_to_validate = self.filtered(lambda p: p.picking_type_id.create_backorder != 'always')
        pickings_to_validate.with_context(cancel_backorder=False)._action_done()
        # Set the state of the pickings to 'done'.

        if self.user_has_groups('stock.group_reception_report'):
            pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
            lines = pickings_show_report.move_ids.filtered(lambda
                                                               m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search(
                    [('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids),
                     ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                    ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                    ('product_qty', '>', 0),
                    ('location_id', 'in', wh_location_ids),
                    ('move_orig_ids', '=', False),
                    ('picking_id', 'not in', pickings_show_report.ids),
                    ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = pickings_show_report.action_view_reception_report()
                    action['context'] = {'default_picking_ids': pickings_show_report.ids}
                    return action
        return True
