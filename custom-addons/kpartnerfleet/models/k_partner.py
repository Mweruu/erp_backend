from odoo import fields, models, api

class KPartner(models.Model):
    _inherit = "res.partner"
   
    vehicles =  fields.One2many("fleet.vehicle", "partner_id", string="Vehicles")
    locations =  fields.One2many("partner.location", "partner_id", string="Locations")