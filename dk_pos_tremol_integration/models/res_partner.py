from odoo import fields, models, api
from odoo.exceptions import ValidationError
import re


class Partner(models.Model):
    _inherit = "res.partner"

    @api.constrains('vat')
    def _check_vat_number(self):
        for record in self:
            if record.vat:
                vat_number = record.vat.upper()
                vat_number_regex = re.compile(r'^[A-Z][0-9]{9}[A-Z]$')
                if not vat_number_regex.match(vat_number):
                    raise ValidationError("PIN Number is not correct.")
