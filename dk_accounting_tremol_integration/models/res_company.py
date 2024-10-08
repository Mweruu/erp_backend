from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    is_set_product_name = fields.Boolean(readonly=False, store=True)
    is_product_name = fields.Text(string='Custom Product Name', readonly=False, store=True)
