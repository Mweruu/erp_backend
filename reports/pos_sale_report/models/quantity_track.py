from datetime import datetime, time
from odoo import models, fields, api


class QuantityTrack(models.Model):
    _name = "quantity.track"
    _description = "Quantity track"
    location = fields.Char(string="Location")

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    def _default_name(self):
        warehouse_name = self.env['stock.warehouse'].search_read([('company_id', '=', self.env.company.id)])
        for wh in warehouse_name:
            return wh['name']

    def _default_warehouse_name(self):
        active_ids = self.env.context.get('active_ids')
        stock_location_id = self.env['stock.location'].browse(active_ids)
        warehouses = self.env['stock.warehouse'].search(['|',
                                                         ('view_location_id', '=', stock_location_id.id),
                                                         ('lot_stock_id', '=', stock_location_id.id),
                                                         ('wh_input_stock_loc_id', '=', stock_location_id.id),
                                                         ('wh_qc_stock_loc_id', '=', stock_location_id.id),
                                                         ('wh_output_stock_loc_id', '=', stock_location_id.id),
                                                         ('wh_pack_stock_loc_id', '=', stock_location_id.id)
                                                         ])
        warehouse_name = ", ".join([w.name for w in warehouses])
        if warehouse_name:
            return warehouse_name
        else:
            return "SLN " + stock_location_id.name

    datetime = fields.Datetime('Datetime')
    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    product_id = fields.Many2one("product.product", required=True)
    user_id = fields.Many2one('res.users', required=True, default=_default_user)
    location = fields.Char(string="Location")
    warehouse_name = fields.Char('Warehouse', index=True, required=True, default=_default_warehouse_name)
    lot_id = fields.Char(string="Lot_id")
    in_date = fields.Datetime('Incoming Date')
    inventory_date = fields.Date('Scheduled Date')
    company_name = fields.Char("Company")
    new_quantity = fields.Char("New Quantity", required=True)
    initial_quantity = fields.Char('Initial Quantity', required=True)
    code = fields.Char('Short Name', size=5)
