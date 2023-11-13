# Copyright 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2013 Camptocamp SA (author: Guewen Baconnier)
# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class SaleOrder(models.Model):
    _inherit = "sale.order"

    workflow_process_id = fields.Many2one(
        comodel_name="sale.workflow.process",
        string="Automatic Workflow",
        ondelete="restrict",
    )
    all_qty_delivered = fields.Boolean(
        compute="_compute_all_qty_delivered",
        string="All quantities delivered",
        store=True,
    )

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    @api.depends("delivery_status")
    def _compute_all_qty_delivered(self):
        for order in self:
            order.all_qty_delivered = order.delivery_status == "full"

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        workflow = self.workflow_process_id
        if not workflow:
            return invoice_vals
        invoice_vals["workflow_process_id"] = workflow.id
        if workflow.invoice_date_is_order_date:
            invoice_vals["invoice_date"] = fields.Date.context_today(
                self, self.date_order
            )
        if workflow.property_journal_id:
            invoice_vals["journal_id"] = workflow.property_journal_id.id
        return invoice_vals

    @api.onchange("workflow_process_id")
    def _onchange_workflow_process_id(self):
        if not self.workflow_process_id:
            return
        workflow = self.workflow_process_id
        if workflow.picking_policy:
            self.picking_policy = workflow.picking_policy
        if workflow.team_id:
            self.team_id = workflow.team_id.id
        if workflow.warning:
            warning = {"title": _("Workflow Warning"), "message": workflow.warning}
            return {"warning": warning}

    def _create_invoices(self, grouped=False, final=False, date=None):
        for order in self:
            if not order.workflow_process_id.invoice_service_delivery:
                continue
            for line in order.order_line:
                if line.qty_delivered_method == "manual" and not line.qty_delivered:
                    line.write({"qty_delivered": line.product_uom_qty})
        return super()._create_invoices(grouped=grouped, final=final, date=date)

    def write(self, vals):
        if vals.get("state") == "sale" and vals.get("date_order"):
            sales_keep_order_date = self.filtered(
                lambda sale: sale.workflow_process_id.invoice_date_is_order_date
            )
            if sales_keep_order_date:
                new_vals = vals.copy()
                del new_vals["date_order"]
                res = super(SaleOrder, sales_keep_order_date).write(new_vals)
                res |= super(SaleOrder, self - sales_keep_order_date).write(vals)
                return res
        return super().write(vals)

    @api.constrains('order_line')
    def _check_product_location(self):
        for order in self:
            for line in order.order_line.filtered(lambda l: l.location_id):
                lines_count = line.search_count(
                    [('order_id', '=', order.id),
                     ('product_id', '=', line.product_id.id),
                     ('location_id', '=', line.location_id.id)])
                if lines_count > 1:
                    raise ValidationError(
                        _("""You cannot add same product %s with the same location %s .""" % (
                            line.product_id.display_name,
                            line.location_id.display_name)))

    def is_amount_to_approve(self):
        self.ensure_one()
        currency = self.company_id.currency_id
        limit_amount = self.company_id.so_double_validation_amount
        limit_amount = currency.compute(limit_amount, self.currency_id)
        return float_compare(limit_amount, self.amount_total, precision_rounding=self.currency_id.rounding) <= 0

    def is_to_approve(self):
        self.ensure_one()
        return (self.company_id.so_double_validation == 'two_step' and self.is_amount_to_approve() and
                not self.user_has_groups('od_sale_order_workflow.sale_order_approval'))

    def action_confirm(self):
        if self.is_to_approve() and self.state in ('draft', 'sent'):
            self.state = 'to_approve'
            return True
        res = super(SaleOrder, self).action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    location_id = fields.Many2one(
        'stock.location', "Location", required=True, domain="[('usage','=','internal')]")


    def _get_parent_view_location(self, location):
        if location.usage == 'view':
            return location
        location = location.location_id
        print(location)
        return self._get_parent_view_location(location)

    def get_operation_type(self, location, operation_type):
        parent_loc_id = self._get_parent_view_location(location)
        warehouse_id = self.env['stock.warehouse'].search([('view_location_id', '=', parent_loc_id.id)])
        operation_type_id = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', warehouse_id.id), ('code', '=', operation_type),
            ('company_id', '=', self.company_id.id)], limit=1)
        return operation_type_id


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        if values.get('sale_line_id', False):
            sale_line_id = self.env['sale.order.line'].sudo().browse(values['sale_line_id'])
            if sale_line_id.location_id:
                picking_type_id = sale_line_id.get_operation_type(sale_line_id.location_id, 'outgoing')
                self.picking_type_id = picking_type_id.id
                self.location_src_id = sale_line_id.location_id.id
        return super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name,
                                                             origin, company_id, values)
