# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class FilterTransfer(models.TransientModel):
    _name = 'filter.transfer'
    _description = "Filter Transfer Report"

    from_date = fields.Date("From Date", required=True)
    to_date = fields.Date("To Date", required=True)

    @api.onchange('from_date', 'to_date')
    def check_date(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise Warning(_("Please enter valid date...!"))

    def print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_date': self.from_date,
                'to_date': self.to_date,
            }
        }
        return self.env.ref('internal_stock_transfer_app.transfer_report_action3').report_action(self, data=data)
