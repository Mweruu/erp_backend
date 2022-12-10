from odoo import models, fields

class KFleet(models.Model):
    _inherit = 'fleet.vehicle'

    # additional fields
    partner_id =  fields.Many2one("res.partner", string="Partner Id", required=True)
    tonnage = fields.Float("Tonnage", required=True)
    
