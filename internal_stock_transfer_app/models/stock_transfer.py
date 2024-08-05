# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockInternalTransfer(models.Model):
    _name = "stock.internal.transfer"
    _description = "Stock Internal Transfer"
    _order = "name"

    @api.model
    def _default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    @api.onchange('dest_warehouse_id', 'source_warehouse_id')
    def change_default_location_id(self):
        company_user = self.env.user.company_id
        dest_warehouse = self.env['stock.warehouse'].search([('id', '=', self.dest_warehouse_id.id)], limit=1)
        source_warehouse = self.env['stock.warehouse'].search([('id', '=', self.source_warehouse_id.id)], limit=1)
        if dest_warehouse or source_warehouse:
            self.location_dest_id = dest_warehouse.lot_stock_id.id
            self.location_id = source_warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    name = fields.Char(
        'Reference', default='/',
        copy=False, index=True, readonly=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    date = fields.Datetime(
        'Date',
        readonly=True, required=True,
        default=fields.Datetime.now)
    line_ids = fields.One2many(
        'stock.internal.transfer.line', 'inventory_id', string='Inventories', copy=False,
        readonly=False,
        states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    move_ids = fields.One2many(
        'stock.move', 'stock_transfer_id', string='Created Moves', copy=False)
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Transfer'),
        ('done', 'Validated')],
                             copy=False, index=True, readonly=True,
                             default='draft')
    source_warehouse_id = fields.Many2one(
        'stock.warehouse', 'Source Warehouse',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_warehouse_id)
    dest_warehouse_id = fields.Many2one(
        'stock.warehouse', 'Destination Warehouse',
        readonly=True,
        default=_default_warehouse_id,
        states={'draft': [('readonly', False)]})
    inventory_location_id = fields.Many2one(
        'stock.location', 'Location', related='source_warehouse_id.lot_stock_id', readonly=True)
    inventory_location_dest_id = fields.Many2one(
        'stock.location', 'Dest Location', related='dest_warehouse_id.lot_stock_id', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Source Location',
        auto_join=True, index=True,
        readonly=True, default=_default_location_id,
        states={'draft': [('readonly', False)]},
        help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")
    transit_location_id = fields.Many2one(
        'stock.location', string='Transit Location',
        auto_join=True, index=True,
        readonly=True, states={'draft': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', string='Destination Location',
        auto_join=True, index=True,
        readonly=True, default=_default_location_id,
        states={'draft': [('readonly', False)]},
        help="Location where the system will stock the finished products.")
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, index=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', _('New')) == _('New'):
    #         if 'company_id' in vals:
    #             vals['name'] = self.env['ir.sequence'].with_company(vals['company_id']).next_by_code(
    #                 'stock.internal.transfer') or _('New')
    #         # vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('stock.internal.transfer') or _('New')
    #         else:
    #             vals['name'] = self.env['ir.sequence'].next_by_code('stock.internal.transfer') or _('New')
    #     result = super(StockInternalTransfer, self).create(vals)
    #     return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_company(vals['company_id']).next_by_code(
                        'stock.internal.transfer') or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('stock.internal.transfer') or _('New')
        result = super(StockInternalTransfer, self).create(vals_list)
        return result

    def action_cancel(self):
        self.write({
            'line_ids': [(5,)],
            'move_ids': [(5,)],
            'state': 'cancel'
        })

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
        })

    def action_start(self):
        for order in self:
            if not order.line_ids:
                raise UserError(_('You can not change stage becuase transfer product empty'))
            for line in order.line_ids:
                if line.transfer_qty == 0.0:
                    raise UserError(
                        _('You can not transfer quantity one %s to another %s becuase Transfer Quantity %s') % (
                            order.location_id.display_name, order.location_dest_id.display_name, line.transfer_qty))
                if self.source_warehouse_id == self.dest_warehouse_id:
                    raise UserError(_('The source and destination warehouse cannot be the same.'))

            order.write({
                'state': 'confirm',
            })

    def action_internal_transfer_move_tree(self):
        form_view_id = self.env.ref('stock.view_move_form').id
        tree_view_id = self.env.ref('stock.view_move_tree').id
        return {
            'name': 'Stock Move',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('stock_transfer_id', 'in', self.ids)],
            'res_model': 'stock.move',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],

        }

    def check_quantity_done(self):
        for record in self:
            if all(line.transfer_qty == line.quantity_done for line in record.line_ids):
                record.write({
                    'state': 'done',
                })
            else:
                record.write({
                    'state': 'confirm',
                })

    def unlink(self):
        if any(move.state not in ('draft', 'cancel') for move in self):
            raise UserError(_('You can only delete draft internal transfer.'))
        return super(StockInternalTransfer, self).unlink()


class StockInternalTransferLine(models.Model):
    _name = "stock.internal.transfer.line"
    _description = "Stock Internal Transfer Line"
    _order = "product_id, inventory_id"

    inventory_id = fields.Many2one(
        'stock.internal.transfer', 'Inventory',
        index=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product',
        index=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure', compute="_compute_product_uom_id", store=True)
    qty_available = fields.Float(compute="_compute_qty_available",
                                 string='Quantity On Hand',
                                 digits='Product Unit of Measure', default=0, store=True)
    transfer_qty = fields.Float(
        'Transfer Quantity',
        digits='Product Unit of Measure', default=0)
    quantity_done = fields.Float(compute="_compute_quantity_done",
                                 string='Receive Quantity',
                                 digits='Product Unit of Measure', default=0, store=True)
    company_id = fields.Many2one(
        'res.company', 'Company', related='inventory_id.company_id',
        index=True, readonly=True, store=True)

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for record in self:
            if record.product_id:
                record.product_uom_id = record.product_id.uom_id.id

    @api.depends('inventory_id', 'inventory_id.move_ids')
    def _compute_quantity_done(self):
        for record in self:
            stock_move_quantity = 0.0
            for stock_move in record.inventory_id.move_ids.filtered(
                    lambda move: move.location_id == record.inventory_id.location_id and move.product_id == record.product_id):
                stock_move_quantity += stock_move.product_uom_qty
            record.quantity_done = stock_move_quantity

    @api.depends('product_id')
    def _compute_qty_available(self):
        for record in self:
            if record.product_id:
                res = record.product_id.with_context(
                    location=record.inventory_id.location_id.id)._compute_quantities_dict(self._context.get('lot_id'),
                                                                                          self._context.get('owner_id'),
                                                                                          self._context.get(
                                                                                              'package_id'),
                                                                                          self._context.get(
                                                                                              'from_date'),
                                                                                          self._context.get('to_date'))
                record.qty_available = res[record.product_id.id]['qty_available']
            else:
                record.qty_available = 0.0


class StockMove(models.Model):
    _inherit = "stock.move"

    stock_transfer_id = fields.Many2one('stock.internal.transfer', 'Stock Transfer')
