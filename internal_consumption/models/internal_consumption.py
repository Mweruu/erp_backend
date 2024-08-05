from odoo import api, fields, models
from odoo.exceptions import UserError
import itertools
from datetime import datetime, date


# Package Class
class InternalConsumption(models.Model):
    _name = 'internal.consumption'
    _inherit = 'mail.thread'
    _description = 'Internal Consumption'
    _rec_name = 'consumption_name'

    consumption_name = fields.Char(required=True, states={
        'draft': [('readonly', False)],
        'ready': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    })

    location_source = fields.Many2one("stock.location", "Stock Source", required=True,
                                      domain="[('usage', '=', 'internal')]", states={
            'draft': [('readonly', False)],
            'ready': [('readonly', True)],
            'done': [('readonly', True)],
            'cancel': [('readonly', True)],
        })

    state = fields.Selection([
        ('draft', "Draft"),
        ('waiting', "Waiting"),
        ('ready', "Ready"),
        ('done', "Done"),
        ('cancel', "Cancelled"),
    ], default='draft',
        string="State", readonly=True, index=True, tracking=True)

    product_lines = fields.One2many('internal.consumption.lines', 'line_id', states={
        'draft': [('readonly', False)],
        'ready': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    })

    def check_availability(self):
        destination_location_id = int(self.env['stock.location'].search([('name', '=', 'Internal Consumption')]).id)

        list_barang = []
        for product_lines in self.env['internal.consumption.lines'].search([('line_id', '=', int(self.id))]):
            available_quantity = self.env['stock.quant']._get_available_quantity(product_lines.product_id,
                                                                                 self.location_source, strict=True)

            if product_lines.reserved_qty == product_lines.product_qty:
                list_barang.append(1)

            elif available_quantity >= product_lines.product_qty:
                new_stock_move = self.env['stock.move'].create({
                    'name': self.consumption_name,
                    'location_id': int(self.location_source),
                    'location_dest_id': destination_location_id,
                    'product_id': product_lines.product_id.id,
                    'product_uom': product_lines.product_uom.id,
                    'product_uom_qty': product_lines.product_qty,
                })
                new_stock_move._action_confirm()
                new_stock_move._action_assign()
                list_barang.append(1)

                product_lines.reserved_qty = product_lines.product_qty
                product_lines.available_qty = available_quantity

            else:
                product_lines.available_qty = available_quantity
                list_barang.append(0)

            if 0 in list_barang:
                self.state = 'draft'
            else:
                self.state = 'ready'

    def unreserve(self):
        for result in self.env['internal.consumption.lines'].search([('line_id', '=', int(self.id))]):
            for stock_move_line in self.env['stock.move'].search(
                    [('reference', '=', str(self.consumption_name)), ('product_id', '=', int(result.product_id))]):
                stock_move_line._do_unreserve()
                stock_move_line.write({'state': 'draft'})
                stock_move_line.unlink()

                result.reserved_qty = 0

                self.state = 'waiting'

    def cancel(self):
        for result in self.env['internal.consumption.lines'].search([('line_id', '=', int(self.id))]):
            for stock_move_line in self.env['stock.move'].search(
                    [('reference', '=', str(self.consumption_name)), ('product_id', '=', int(result.product_id))]):
                stock_move_line._do_unreserve()
                stock_move_line.write({'state': 'draft'})
                stock_move_line.unlink()

                result.reserved_qty = 0

                self.state = 'cancel'

    def validate(self):
        for product in self.env['stock.move'].search(
                [('reference', '=', str(self.consumption_name)), ('state', '=', 'assigned')]):
            product.move_line_ids.write({'qty_done': product.product_qty})
            product._action_done()

        journal_entry_list = []
        for product in self.product_lines:
            journal_entry_line = [(0, 0, {
                'name': str(self.consumption_name) + str(' - ') + str(product.product_id.name),
                'date': self.create_date.date(),
                'account_id': product.account.id,
                'debit': product.product_id.standard_price * product.product_qty,
                'credit': 0,
            }),

                                  (0, 0, {
                                      'name': str(self.consumption_name) + str(' - ') + str(product.product_id.name),
                                      'date': self.create_date.date(),
                                      'account_id': product.product_id.categ_id.property_stock_account_output_categ_id.id,
                                      'debit': 0,
                                      'credit': product.product_id.standard_price * product.product_qty,
                                  })]

            journal_entry_list.append(journal_entry_line)

        line_id = (list(itertools.chain.from_iterable(journal_entry_list)))

        create_journal = self.env['account.move'].create({
            'ref': self.consumption_name,
            'date': self.create_date.date(),
            'line_ids': line_id,
        })

        create_journal.action_post()

        self.state = 'done'


class InternalConsumptionLines(models.Model):
    _name = 'internal.consumption.lines'
    _description = 'Allows you to consume your product for company internal use'

    account = fields.Many2one("account.account", "Account", required=True)

    line_id = fields.Many2one('internal.consumption', invisible=True)
    product_id = fields.Many2one('product.product', string="Product Name")
    employee = fields.Many2one("hr.employee", "Employee", required=True)
    product_qty = fields.Float(string="Qty", digits=(12, 2))
    available_qty = fields.Float(string="Available Qty", digits=(12, 2))
    reserved_qty = fields.Float(string="Reserved Qty", digits=(12, 2))
    product_uom = fields.Many2one('uom.uom', string="Unit of Measure")
    list_price = fields.Float('Sales Price', default=0.0)
    standard_price = fields.Float('Cost Price', default=0.0)
    unit_price = fields.Float('Unit Price', default=0.0)

    @api.onchange('product_id')
    def _fetch_uom(self):
        self.product_uom = self.product_id.uom_id.id
        self.list_price = self.product_id.list_price
        self.standard_price = self.product_id.standard_price

    @api.onchange('product_id', 'product_qty', 'standard_price')
    def _compute_unit_price(self):
        self.unit_price = self.product_qty * self.standard_price
