from odoo import models


class Location(models.Model):
    _inherit = "stock.location"

    def should_bypass_reservation(self):
        self.ensure_one()
        return True
