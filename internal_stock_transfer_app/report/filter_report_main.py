# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning


class TransferReport(models.AbstractModel):
    _name = 'report.internal_stock_transfer_app.template_report3'
    _description = "Transfer Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        get_to = data['form']['to_date']
        get_from = data['form']['from_date']
        docs = []
        to_date = datetime.strptime(get_to, '%Y-%m-%d').date()
        from_date = datetime.strptime(get_from, '%Y-%m-%d').date()

        transfer = self.env['stock.internal.transfer'].search([('date', '>=', from_date), ('date', '<=', to_date)])
        if not transfer:
            raise Warning(_("Internal Transfer is not available in this Date range."))

        for each in transfer:
            for line in each.line_ids:
                docs.append({
                    'product_id': line.product_id.name,
                    'quantity': line.quantity_done,
                    'product_uom_id': line.product_uom_id.name,
                    'warehouse': each.dest_warehouse_id.name,
                })
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'report_date': fields.Date.today(),
            'from_date': from_date,
            'to_date': to_date,
            'docs': docs,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
