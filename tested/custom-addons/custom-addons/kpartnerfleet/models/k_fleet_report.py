from datetime import datetime, time
from odoo import models, fields, api

FUEL_TYPES = [
    ('diesel', 'Diesel'),
    ('gasoline', 'Gasoline'),
    ('hybrid', 'Hybrid Diesel'),
    ('full_hybrid_gasoline', 'Hybrid Gasoline'),
    ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
    ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
    ('cng', 'CNG'),
    ('lpg', 'LPG'),
    ('hydrogen', 'Hydrogen'),
    ('electric', 'Electric')]


class FleetReport(models.Model):
    _name = "fleet.report"

    def _default_name(self):
        name = self.env['fleet.vehicle'].search_read([('model_id', '=', self.model_id)])
        return name

    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())
    name = fields.Char(compute="_compute_vehicle_name", store=True)
    license_plate = fields.Char(tracking=True, help='License plate number of the vehicle (i = plate number for a car)')
    driver_id = fields.Many2one('res.partner', 'Driver')
    future_driver_id = fields.Many2one('res.partner', 'Future Driver')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', 'Brand')
    odometer_count = fields.Integer(compute="_compute_count_all", string='Odometer')
    acquisition_date = fields.Date('Immatriculation Date', required=False, default=fields.Date.today)
    color = fields.Char(help='Color of the vehicle', compute='_compute_model_fields', store=True, readonly=False)
    location = fields.Char(help='Location of the vehicle (garage, ...)')
    seats = fields.Integer('Seats Number', help='Number of seats of the vehicle', compute='_compute_model_fields',
                           store=True, readonly=False)
    model_year = fields.Char('Model Year', help='Year of the model', compute='_compute_model_fields', store=True,
                             readonly=False)
    doors = fields.Integer('Doors Number', help='Number of doors of the vehicle', compute='_compute_model_fields',
                           store=True, readonly=False)
    fuel_type = fields.Selection(FUEL_TYPES, 'Fuel Type', help='Fuel Used by the vehicle',
                                 compute='_compute_model_fields', store=True, readonly=False)
    vehicle_type = fields.Selection(related='model_id.vehicle_type')
