# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockProductProduce(models.TransientModel):
    _name = "stock.product.produce"
    _description = "Stock Product Produce"

    @api.model
    def default_get(self, fields):
        res = super(StockProductProduce, self).default_get(fields)
        if self._context and self._context.get('active_id'):
            stock_transfer = self.env['stock.internal.transfer'].browse(self._context['active_id'])
            if 'source_warehouse_id' in fields:
                res['source_warehouse_id'] = stock_transfer.source_warehouse_id.id
            if 'dest_warehouse_id' in fields:
                res['dest_warehouse_id'] = stock_transfer.dest_warehouse_id.id
            if 'location_id' in fields:
                res['location_id'] = stock_transfer.location_id.id
            if 'location_dest_id' in fields:
                res['location_dest_id'] = stock_transfer.location_dest_id.id
            if 'stock_produce_line_ids' in fields:
                lines = []
                for stock in stock_transfer.line_ids.filtered(lambda self: self.transfer_qty != self.quantity_done):
                    lines.append({
                        'qty_available': stock.qty_available or 0.0,
                        'transfer_qty': stock.transfer_qty or 0.0,
                        'transfer_qty_stock': stock.transfer_qty or 0.0,
                        'quantity_done': stock.transfer_qty,
                        'product_uom_id': stock.product_uom_id.id,
                        'product_id_stock': stock.product_id.id,
                        'product_id': stock.product_id.id,
                        'source_warehouse_id': stock_transfer.source_warehouse_id.id,
                        'dest_warehouse_id': stock_transfer.dest_warehouse_id.id,
                        'location_id': stock_transfer.location_id.id,
                        'location_dest_id': stock_transfer.location_dest_id.id,
                        'prev_receive_qty_stock': stock.quantity_done,
                        'prev_receive_qty': stock.quantity_done
                    })
                res['stock_produce_line_ids'] = [(0, 0, x) for x in lines]
        return res

    source_warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse')
    dest_warehouse_id = fields.Many2one('stock.warehouse', 'Destination Warehouse')
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    stock_produce_line_ids = fields.One2many('stock.product.produce.line', 'product_produce_id',
                                             string='Product to Track')

    def do_produce(self):
        stock_transfer = self.env['stock.internal.transfer'].browse(self._context['active_id'])
        for line in self.stock_produce_line_ids:
            if line.quantity_done > line.transfer_qty:
                raise UserError(
                    _('You plan to transfer %s %s of %s but you only have %s %s available stock in %s location.') % \
                    (line.quantity_done, line.product_uom_id.name, line.product_id.name, line.transfer_qty,
                     line.product_id.uom_id.name, line.location_id.display_name))
            line._get_raw_move_data(stock_transfer)
            # line._generate_finished_moves(stock_transfer)
        stock_transfer.check_quantity_done()


class StockProductProduceLine(models.TransientModel):
    _name = "stock.product.produce.line"
    _description = "Stock Product Produce Line"

    product_produce_id = fields.Many2one('stock.product.produce')
    product_id_stock = fields.Many2one(
        'product.product', 'Product Stock',
        index=True)
    product_id = fields.Many2one('product.product', related='product_id_stock',
                                 string='Product', readonly=True, store=False)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', compute="_compute_product_uom_id",
                                     store=True)
    qty_available = fields.Float(compute="_compute_qty_available",
                                 string='Quantity On Hand',
                                 digits='Product Unit of Measure', default=0, store=True)
    transfer_qty_stock = fields.Float(
        'Transfer Quantity Stock',
        digits='Product Unit of Measure', default=0)
    transfer_qty = fields.Float(related='transfer_qty_stock',
                                string='Transfer Quantity',
                                digits='Product Unit of Measure', readonly=True, store=False)
    quantity_done = fields.Float(
        'Receive Quantity',
        digits='Product Unit of Measure', default=0)
    prev_receive_qty_stock = fields.Float(
        'Total Receive Quantity Stock',
        digits='Product Unit of Measure', default=0)
    prev_receive_qty = fields.Float(related='prev_receive_qty_stock',
                                    string='Total Receive Quantity',
                                    digits='Product Unit of Measure', readonly=True, store=False)
    source_warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse')
    dest_warehouse_id = fields.Many2one('stock.warehouse', 'Destination Warehouse')
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')

    @api.onchange('quantity_done', 'transfer_qty')
    def onchange_qty_check(self):
        for record in self:
            if record.quantity_done > record.transfer_qty:
                raise UserError(
                    _('You plan to transfer %s %s of %s but you only have %s %s available stock in %s location.') % \
                    (record.quantity_done, record.product_uom_id.name, record.product_id.name, record.transfer_qty,
                     record.product_id.uom_id.name, record.location_id.display_name))

    @api.depends('product_id')
    def _compute_qty_available(self):
        for record in self:
            if record.product_id:
                res = record.product_id.with_context(location=record.location_id.id)._compute_quantities_dict(
                    self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),
                    self._context.get('from_date'), self._context.get('to_date'))
                record.qty_available = res[record.product_id.id]['qty_available']
            else:
                record.qty_available = 0.0

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        self.product_uom_id = self.product_id.uom_id.id

    def _generate_finished_moves(self, stock_transfer):
        move_vals = {
            'name': stock_transfer.name,
            'date': stock_transfer.date,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.quantity_done,
            'location_id': self.product_id.property_stock_production.id,
            # 'location_id': stock_transfer.transit_location_id.id,
            'location_dest_id': stock_transfer.location_dest_id.id,
            'company_id': stock_transfer.company_id.id,
            'stock_transfer_id': stock_transfer.id,
            'warehouse_id': self.dest_warehouse_id.id,
            'origin': stock_transfer.name,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'product_uom_id': self.product_uom_id.id,
                                      'qty_done': self.quantity_done,
                                      'location_id': self.product_id.property_stock_production.id,
                                      # 'location_id': stock_transfer.transit_location_id.id,
                                      'location_dest_id': stock_transfer.location_dest_id.id,
                                      })]
        }
        move = self.env['stock.move'].create(move_vals)
        move._action_done()
        return move

    def _get_raw_move_data(self, stock_transfer):
        move_vals = {
            'name': stock_transfer.name,
            'date': stock_transfer.date,
            'stock_transfer_id': stock_transfer.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.quantity_done,
            'location_id': stock_transfer.location_id.id,
            'location_dest_id': stock_transfer.location_dest_id.id,
            # 'location_dest_id': self.product_id.property_stock_production.id,
            # 'location_dest_id': stock_transfer.transit_location_id.id,
            'company_id': stock_transfer.company_id.id,
            'price_unit': self.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': stock_transfer.name,
            'warehouse_id': self.source_warehouse_id.id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom_id.id,
                'qty_done': self.quantity_done,
                'location_id': stock_transfer.location_id.id,
                'location_dest_id': stock_transfer.location_dest_id.id,
                # 'location_dest_id': self.product_id.property_stock_production.id,
                # 'location_dest_id': stock_transfer.transit_location_id.id,
            })]
        }
        move = self.env['stock.move'].create(move_vals)
        move._action_done()
        return move
