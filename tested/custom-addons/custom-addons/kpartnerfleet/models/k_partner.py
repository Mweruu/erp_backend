import phonenumbers

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class KPartner(models.Model):
    _inherit = "res.partner"

    vehicles = fields.One2many("fleet.vehicle", "partner_id", string="Vehicles")
    phone = fields.Char()
    locations = fields.One2many("partner.location", "partner_id", string="Locations")

    @api.constrains('phone')
    def _check_phone_number(self):
        for record in self:
            phonenum = str(record.phone).split(',')
            if len(phonenum) > 0:
                for num in phonenum:
                    phone_number = phonenumbers.parse(num, "RO")
                    valid_number = phonenumbers.is_valid_number(phone_number)
                    if not valid_number:
                        raise ValidationError("Invalid phone number")
