from odoo import models, fields


# locations for a partner
class KLocations(models.Model):
    _name = 'partner.location'

    name = fields.Char("Location", required=True)
    partner_id = fields.Many2one("res.partner")
