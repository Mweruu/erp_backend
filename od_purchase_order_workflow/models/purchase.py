# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approval_level_id = fields.Many2one(
        'sh.purchase.approval.config', string="Approval Level", compute="compute_approval_level")
    state = fields.Selection(
        selection_add=[('waiting_for_approval', 'Waiting for Approval'), ('reject', 'Reject'), ('purchase',)])
    level = fields.Integer(string="Next Approval Level", readonly=True)
    user_ids = fields.Many2many('res.users', string="Users", readonly=True)
    group_ids = fields.Many2many('res.groups', string="Groups", readonly=True)
    is_boolean = fields.Boolean(
        string="Boolean", compute="compute_is_boolean", search='_search_is_boolean')
    approval_info_line = fields.One2many(
        'sh.approval.info', 'purchase_order_id', readonly=True)
    rejection_date = fields.Datetime(string="Reject Date", readonly=True)
    reject_by = fields.Many2one('res.users', string="Reject By", readonly=True)
    reject_reason = fields.Char(string="Reject Reason", readonly=True)
    ywt_purchase_order_automation_id = fields.Many2one('ywt.purchase.order.automation', string='Order Automation')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id.is_auto_purchase_order_automation:
            self.ywt_purchase_order_automation_id = self.partner_id.ywt_purchase_order_automation_id
        return res

    def action_purchase_order_automation_method(self):
        print("action_purchase_order_automation_method here")
        self.env['ywt.purchase.order.automation'].with_context(
            {"purchase_ids": self.ids}).ywt_main_purchase_order_automation_method()

    def compute_is_boolean(self):
        if self.env.user.id in self.user_ids.ids or any(
                item in self.env.user.groups_id.ids for item in self.group_ids.ids):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def _search_is_boolean(self, operator, value):
        results = []
        if value:
            po_ids = self.env['purchase.order'].search([])
            if po_ids:
                for po in po_ids:
                    if self.env.user.id in po.user_ids.ids or any(
                            item in self.env.user.groups_id.ids for item in po.group_ids.ids):
                        results.append(po.id)
        return [('id', 'in', results)]

    def button_confirm(self):
        if self.env.context.get('auto_workflow_set'):
            return super(PurchaseOrder, self).button_confirm()
        template_id = self.env.ref("od_purchase_order_workflow.email_template_for_approve_purchase_order")
        if self.approval_level_id.purchase_approval_line:
            self.write({
                'state': 'waiting_for_approval'
            })
            lines = self.approval_level_id.purchase_approval_line

            self.approval_info_line = False
            for line in lines:
                dictt = []
                if line.approve_by == 'group':
                    dictt.append((0, 0, {
                        'level': line.level,
                        'user_ids': False,
                        'group_ids': [(6, 0, line.group_ids.ids)],
                    }))

                if line.approve_by == 'user':
                    dictt.append((0, 0, {
                        'level': line.level,
                        'user_ids': [(6, 0, line.user_ids.ids)],
                        'group_ids': False,
                    }))

                self.update({
                    'approval_info_line': dictt
                })

            if lines[0].approve_by == 'group':
                self.write({
                    'level': lines[0].level,
                    'group_ids': [(6, 0, lines[0].group_ids.ids)],
                    'user_ids': False
                })

                users = self.env['res.users'].search(
                    [('groups_id', 'in', lines[0].group_ids.ids)])

                if template_id and users:
                    for user in users:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if users:
                    for user in users:
                        notifications.append(
                            (user.partner_id, 'sh_notification_info',
                             {'title': _('Notitification'),
                              'message': 'You have approval notification for Purchase order %s' % (self.name)
                              }))
                    self.env['bus.bus']._sendmany(notifications)

            if lines[0].approve_by == 'user':
                self.write({
                    'level': lines[0].level,
                    'user_ids': [(6, 0, lines[0].user_ids.ids)],
                    'group_ids': False
                })

                if template_id and lines[0].user_ids:
                    for user in lines[0].user_ids:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if lines[0].user_ids:
                    for user in lines[0].user_ids:
                        notifications.append(
                            (user.partner_id, 'sh_notification_info',
                             {'title': _('Notitification'),
                              'message': 'You have approval notification for Purchase order %s' % (self.name)
                              }))
                    self.env['bus.bus']._sendmany(notifications)

        elif self.ywt_purchase_order_automation_id:
            print("got here")
            self.action_purchase_order_automation_method()
        else:
            print("and got here")

            super(PurchaseOrder, self).button_confirm()

    @api.depends('amount_untaxed', 'amount_total')
    def compute_approval_level(self):
        if self.company_id.approval_based_on:
            if self.company_id.approval_based_on == 'untaxed_amount':

                purchase_approvals = self.env['sh.purchase.approval.config'].search(
                    [('min_amount', '<', self.amount_untaxed), ('company_ids.id', 'in', [self.env.company.id])])

                listt = []
                for purchase_approval in purchase_approvals:
                    listt.append(purchase_approval.min_amount)

                if listt:
                    purchase_approval = purchase_approvals.filtered(
                        lambda x: x.min_amount == max(listt))

                    self.update({
                        'approval_level_id': purchase_approval[0].id
                    })
                else:
                    self.approval_level_id = False

            if self.company_id.approval_based_on == 'total':

                purchase_approvals = self.env['sh.purchase.approval.config'].search(
                    [('min_amount', '<', self.amount_total), ('company_ids.id', 'in', [self.env.company.id])])

                listt = []
                for purchase_approval in purchase_approvals:
                    listt.append(purchase_approval.min_amount)

                if listt:
                    purchase_approval = purchase_approvals.filtered(
                        lambda x: x.min_amount == max(listt))

                    self.update({
                        'approval_level_id': purchase_approval[0].id
                    })
                else:
                    self.approval_level_id = False

        else:
            self.approval_level_id = False

    def action_approve_order(self):
        template_id = self.env.ref("od_purchase_order_workflow.email_template_for_approve_purchase_order")

        info = self.approval_info_line.filtered(
            lambda x: x.level == self.level)

        if info:
            info.status = True
            info.approval_date = datetime.now()
            info.approved_by = self.env.user

        line_id = self.env['sh.purchase.approval.line'].search(
            [('purchase_approval_config_id', '=', self.approval_level_id.id), ('level', '=', self.level)])

        next_line = self.env['sh.purchase.approval.line'].search(
            [('purchase_approval_config_id', '=', self.approval_level_id.id), ('id', '>', line_id.id)], limit=1)

        if next_line:
            if next_line.approve_by == 'group':
                self.write({
                    'level': next_line.level,
                    'group_ids': [(6, 0, next_line.group_ids.ids)],
                    'user_ids': False
                })
                users = self.env['res.users'].search(
                    [('groups_id', 'in', next_line.group_ids.ids)])

                if template_id and users and self.approval_level_id.is_boolean:
                    for user in users:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email, 'email_cc': self.user_id.email})

                if template_id and users and not self.approval_level_id.is_boolean:
                    for user in users:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if users:
                    for user in users:
                        notifications.append(
                            (user.partner_id, 'sh_notification_info',
                             {'title': _('Notitification'),
                              'message': 'You have approval notification for Purchase order %s' % (self.name)
                              }))
                    self.env['bus.bus']._sendmany(notifications)

            if next_line.approve_by == 'user':
                self.write({
                    'level': next_line.level,
                    'user_ids': [(6, 0, next_line.user_ids.ids)],
                    'group_ids': False
                })
                if template_id and next_line.user_ids and self.approval_level_id.is_boolean:
                    for user in next_line.user_ids:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email, 'email_cc': self.user_id.email})

                if template_id and next_line.user_ids and not self.approval_level_id.is_boolean:
                    for user in next_line.user_ids:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if next_line.user_ids:
                    for user in next_line.user_ids:
                        notifications.append(
                            (user.partner_id, 'sh_notification_info',
                             {'title': _('Notitification'),
                              'message': 'You have approval notification for Purchase order %s' % (self.name)
                              }))
                    self.env['bus.bus']._sendmany(notifications)


        else:
            template_id = self.env.ref(
                "od_purchase_order_workflow.email_template_for_confirm_purchase_order")
            if template_id:
                template_id.sudo().send_mail(self.id, force_send=True, email_values={
                    'email_from': self.env.user.email, 'email_to': self.user_id.email})

            notifications = []
            if self.user_id:
                notifications.append(
                    (self.user_id.partner_id, 'sh_notification_info',
                     {'title': _('Notitification'),
                      'message': 'Dear User!! your Purchase order %s is confirmed' % (self.name)
                      }))
                self.env['bus.bus']._sendmany(notifications)

            self.write({
                'level': False,
                'group_ids': False,
                'user_ids': False,
                'state': 'sent',
            })
            if self.ywt_purchase_order_automation_id:
                self.action_purchase_order_automation_method()
            else:
                super(PurchaseOrder, self).button_confirm()

    def action_reset_to_draft(self):
        self.write({
            'state': 'draft'
        })

    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            order = order.with_company(order.company_id)
            for line in order.order_line.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.picking_type_id.id == line.picking_type_id.id)
                if not pickings:
                    res = order.with_context(line_picking_type_id=line.picking_type_id.id)._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                else:
                    picking = pickings[0]
                moves = line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return True

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        ctx = self.env.context
        if ctx.get('line_picking_type_id'):
            type_id = self.env['stock.picking.type'].browse(ctx['line_picking_type_id'])
            res.update({'picking_type_id': ctx['line_picking_type_id'],
                        'company_id': type_id.company_id.id,
                        'location_dest_id': type_id.default_location_dest_id.id,
                        })
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    picking_type_id = fields.Many2one('stock.picking.type', string='Deliver To')

    @api.onchange('product_id')
    def onchange_custom_product_id(self):
        self.picking_type_id = self.order_id.picking_type_id

    def _prepare_stock_moves(self, picking):
        template = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        if template:
            for each in template:
                each.update({'picking_type_id': self.picking_type_id.id,
                             'company_id': picking.company_id.id,
                             'route_ids': self.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.picking_type_id.warehouse_id.route_ids])] or [],
                             'location_dest_id': self.picking_type_id.default_location_dest_id.id
                })
        return template

    def _create_or_update_picking(self):
        for line in self:
            if line.product_id and line.product_id.type in ('product', 'consu'):
                # Prevent decreasing below received quantity
                if float_compare(line.product_qty, line.qty_received, line.product_uom.rounding) < 0:
                    raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
                                      'Create a return first.'))

                if float_compare(line.product_qty, line.qty_invoiced, line.product_uom.rounding) == -1:
                    # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                    # inviting the user to create a refund.
                    line.invoice_lines[0].move_id.activity_schedule(
                        'mail.mail_activity_data_warning',
                        note=_('The quantities on your purchase order indicate less than billed. You should ask for a refund.'))

                # If the user increased quantity of existing line or created a new line
                pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit', 'customer') and x.picking_type_id.id == line.picking_type_id.id)
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.order_id.with_context(line_picking_type_id=line.picking_type_id.id)._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                moves = line._create_stock_moves(picking)
                moves._action_confirm()._action_assign()
