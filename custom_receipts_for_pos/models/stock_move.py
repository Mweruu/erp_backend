from odoo import _, api, Command, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    # def action_confirm(self):
    #     res = super().action_confirm()
    #     # for picking in self:
    #     for picking in self.picking_ids:
    #         for stock_move in picking.move_ids_without_package:
    #             if stock_move.move_line_ids:
    #                 stock_move.move_line_ids.update({
    #                     'qty_done': stock_move.product_uom_qty,
    #                 })
    #             else:
    #                 self.env['stock.move.line'].create({
    #                     'picking_id': picking.id,
    #                     'move_id': stock_move.id,
    #                     'date': stock_move.date,
    #                     'reference': stock_move.reference,
    #                     'origin': stock_move.origin,
    #                     'qty_done': stock_move.product_uom_qty,
    #                     'product_id': stock_move.product_id.id,
    #                     'product_uom_id': stock_move.product_uom.id,
    #                     'location_id': stock_move.location_id.id,
    #                     'location_dest_id': stock_move.location_dest_id.id
    #                 })
    #         picking.button_validate()
    #         if picking.state != 'done':
    #             sms = self.env['confirm.stock.sms'].create({
    #                 'pick_ids': [(4, picking.id)],
    #             })
    #             sms.send_sms()
    #             picking.button_validate()
    #     return res

    def _action_assign(self, force_qty=False):
        res = super(StockMove, self)._action_assign(force_qty=force_qty)
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `reserved_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        StockMoves = self.env['stock.move']
        assigned_moves_ids = OrderedSet()
        partially_available_moves_ids = OrderedSet()
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        # Once the quantities are assigned, we want to find a better destination location thanks
        # to the putaway rules. This redirection will be applied on moves of `moves_to_redirect`.
        moves_to_redirect = OrderedSet()
        moves_to_assign = self
        if not force_qty:
            moves_to_assign = self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available'])
        for move in moves_to_assign:
            rounding = roundings[move]
            if not force_qty:
                missing_reserved_uom_quantity = move.product_uom_qty
            else:
                missing_reserved_uom_quantity = force_qty
            missing_reserved_uom_quantity -= reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity,
                                                                           move.product_id.uom_id,
                                                                           rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.move_orig_ids:
                    available_move_lines = move._get_available_move_lines(assigned_moves_ids,
                                                                          partially_available_moves_ids)
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        qty_added = min(missing_reserved_quantity, quantity)
                        move_line_vals = move._prepare_move_line_vals(qty_added)
                        move_line_vals.update({
                            'location_id': location_id.id,
                            'lot_id': lot_id.id,
                            'lot_name': lot_id.name,
                            'owner_id': owner_id.id,
                            'package_id': package_id.id,
                        })
                        move_line_vals_list.append(move_line_vals)
                        missing_reserved_quantity -= qty_added
                        if float_is_zero(missing_reserved_quantity,
                                         precision_rounding=move.product_id.uom_id.rounding):
                            break

                if missing_reserved_quantity and move.product_id.tracking == 'serial' and (
                        move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                elif missing_reserved_quantity:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                       ml.location_id == move.location_id and
                                                                       ml.location_dest_id == move.location_dest_id and
                                                                       ml.picking_id == move.picking_id and
                                                                       not ml.lot_id and
                                                                       not ml.package_id and
                                                                       not ml.owner_id)
                    if to_update:
                        to_update[0].reserved_uom_qty += move.product_id.uom_id._compute_quantity(
                            missing_reserved_quantity, move.product_uom, rounding_method='HALF-UP')
                    else:
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves_ids.add(move.id)
                moves_to_redirect.add(move.id)
            else:
                if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    assigned_moves_ids.add(move.id)
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves_ids.add(move.id)
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = move._get_available_quantity(move.location_id,
                                                                      package_id=forced_package_id)
                    print("available_quantity", available_quantity)
                    if available_quantity <= 0:
                        print("aq", available_quantity)
                        to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                           ml.location_id == move.location_id and
                                                                           ml.location_dest_id == move.location_dest_id and
                                                                           ml.picking_id == move.picking_id and
                                                                           not ml.lot_id and
                                                                           not ml.package_id and
                                                                           not ml.owner_id)
                        if to_update:
                            print("toupdate")
                            to_update[0].reserved_uom_qty += move.product_id.uom_id._compute_quantity(
                                missing_reserved_quantity, move.product_uom, rounding_method='HALF-UP')
                        else:
                            print("else")
                            move_line_vals_list.append(
                                move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                    assigned_moves_ids.add(move.id)
                    moves_to_redirect.add(move.id)
                    # continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id,
                                                                    package_id=forced_package_id, strict=False)
                    print("tq", taken_quantity)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    moves_to_redirect.add(move.id)
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves_ids.add(move.id)
                    else:
                        partially_available_moves_ids.add(move.id)
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    available_move_lines = move._get_available_move_lines(assigned_moves_ids,
                                                                          partially_available_moves_ids)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.reserved_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id,
                                                     move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(
                                move_line.location_id, move_line.lot_id, move_line.result_package_id,
                                move_line.owner_id)] -= move_line.reserved_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('reserved_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = move._get_available_quantity(location_id, lot_id=lot_id,
                                                                          package_id=package_id, owner_id=owner_id,
                                                                          strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity),
                                                                        location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        moves_to_redirect.add(move.id)
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves_ids.add(move.id)
                            break
                        partially_available_moves_ids.add(move.id)
            if move.product_id.tracking == 'serial':
                move.next_serial_count = move.product_uom_qty

        self.env['stock.move.line'].create(move_line_vals_list)
        StockMoves.browse(partially_available_moves_ids).write({'state': 'partially_available'})
        StockMoves.browse(assigned_moves_ids).write({'state': 'assigned'})
        if not self.env.context.get('bypass_entire_pack'):
            self.picking_id._check_entire_pack()
        StockMoves.browse(moves_to_redirect).move_line_ids._apply_putaway_strategy()
        return res


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None,
                                  owner_id=None, strict=False):
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(
                quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped(
                    'quantity')) - sum(quants.mapped('reserved_quantity'))
            if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to reserve more products of %s than you have in stock.',
                                  product_id.display_name))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            print("avq", available_quantity, "quantity", quantity)
            if quantity <= 0:
                print("goooot here")
                return reserved_quants
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.',
                                  product_id.display_name))
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity,
                                                                                     precision_rounding=rounding):
                break
        return super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity, lot_id,
                                                                 package_id,
                                                                 owner_id, strict)
