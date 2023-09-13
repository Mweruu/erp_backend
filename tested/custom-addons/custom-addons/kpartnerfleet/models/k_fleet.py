from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KFleet(models.Model):
    _inherit = 'fleet.vehicle'

    # additional fields
    partner_id = fields.Many2one("res.partner", string="Partner Id", required=True)
    tonnage = fields.Float("Tonnage", required=True)
    phone = fields.Char()

    @api.constrains('tonnage')
    def _check_tonnage(self):
        for record in self:
            if record.tonnage <= 0.00:
                raise ValidationError("Tonnage should be greater than 0")
