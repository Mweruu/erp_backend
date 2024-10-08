# Copyright 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2013 Camptocamp SA (author: Guewen Baconnier)
# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)

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

    state = fields.Selection(
        selection_add=[('to_approve', 'To Approve'),
                       ('confirmed', 'Confirmed')])

    is_invoiced_kk = fields.Boolean(string="Is Invoiced", compute='_compute_sale_order_state', store=True, default=False)

    @api.depends('invoice_status')
    def _compute_sale_order_state(self):
        for order in self:
            if not order.is_invoiced_kk:
                if order.invoice_status == 'invoiced':
                    order.is_invoiced_kk = True

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

    def is_below_limit(self):
        self.ensure_one()
        currency = self.company_id.currency_id
        limit_amount = self.company_id.so_double_validation_amount
        limit_amount = currency.compute(limit_amount, self.currency_id)
        return float_compare(limit_amount, self.amount_total, precision_rounding=self.currency_id.rounding) == 1

    def is_above_limit(self):
        self.ensure_one()
        currency = self.company_id.currency_id
        limit_amount = self.company_id.so_double_validation_amount
        limit_amount = currency.compute(limit_amount, self.currency_id)
        return float_compare(limit_amount, self.amount_total, precision_rounding=self.currency_id.rounding) <= 0

    def is_to_approve(self):
        self.ensure_one()
        if (self.company_id.so_double_validation == 'two_step' and (self.is_below_limit() or self.is_above_limit()) and
                not (self.user_has_groups('dk_sale_automatic_workflow.sale_order_approval') or self.user_has_groups(
                    'sales_team.group_sale_manager'))):
            return True

    def is_price_allowed(self, ):
        if self.user_has_groups('dk_sale_automatic_workflow.sales_price_modify') or self.user_has_groups(
                'sales_team.group_sale_manager'):
            return True

        is_set_limit_pct = self.env['ir.config_parameter'].sudo().get_param(
            'dk_sale_automatic_workflow.sale_set_percentage_range_bool')

        limit_pct = self.env['ir.config_parameter'].sudo().get_param(
            'dk_sale_automatic_workflow.sale_set_percentage_range')

        if not is_set_limit_pct:
            return True

        order_lines = self.env['sale.order.line'].search([('order_id', '=', self.id)])
        priceAllowed = True

        for line in order_lines:
            product = line.product_id
            list_price = product.product_tmpl_id.list_price
            difference = line.price_unit - list_price
            absolute_percentage = abs(difference / list_price * 100)
            if absolute_percentage > float(limit_pct):
                priceAllowed = False
                break

        return priceAllowed

    def _can_confirm_from_all_states(self):
        """
        Check if the order can be confirmed based on the current state and user groups.
        Returns True if the state should be changed to 'confirmed', False otherwise.
        """
        if self.state in ['to_approve', 'draft', 'sent']:
            if self.user_has_groups('dk_sale_automatic_workflow.sale_order_approval') or \
                    self.user_has_groups('sales_team.group_sale_manager'):
                _logger.info(f"Order {self.id} state can be changed to 'confirmed'.")
                return True
        return False

    def action_save_order(self):
        if not self.is_price_allowed():
            _logger.error("Sale price on one of the products is not allowed.")
            raise ValidationError(_('The Sale price on one of the products is not allowed.'))
        if self.state in ['draft', 'sent']:
            if self.is_to_approve():
                _logger.info(f"Order {self.id} state changed to 'to_approve'")
                self.state = 'to_approve'

        if self._can_confirm_from_all_states():
            _logger.info(f"Order {self.id} state changed to 'confirmed'")
            self.state = 'confirmed'
            return True

        _logger.warning(f"Order {self.id} did not transition to any recognized state.")
        return False


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    location_id = fields.Many2one(
        'stock.location', "Location", required=True, domain="[('usage','=','internal'),('name', '=', 'Stock')]")

    def _get_parent_view_location(self, location):
        if location.usage == 'view':
            return location
        location = location.location_id
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
