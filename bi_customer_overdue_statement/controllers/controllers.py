# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class SupplierPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        if 'supplier_rfq_count' not in counters:
            customer = request.env.user.partner_id.company_id
            if customer.customer_statement_portal:
                values['supplier_rfq_count'] = len(request.env.user.partner_id.balance_invoice_ids)
            if customer.supplier_statement_portal:
                values['supplier_count'] = len(request.env.user.partner_id.supplier_invoice_ids)

        return values

    @http.route(['/my/statements'], type='http', auth="user", website=True)
    def portal_my_statements(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        partner = request.env['res.partner']
        partners = request.env.user.partner_id
        supplier_rfq_count = len(request.env.user.partner_id.balance_invoice_ids)
        pager = portal_pager(
            url='/my/statements',
            total=supplier_rfq_count,
            page=page,
            step=self._items_per_page
        )
        supplier_rfq = request.env.user.partner_id.balance_invoice_ids
        partners_data = supplier_rfq
        values = {
            'date': date_begin,
            'page_name': 'partners_data',
            'partners_data': partners_data,
            'partners': partners,
            'default_url': '/my/statements',
            'pager': pager,
        }

        return request.render("bi_customer_overdue_statement.portal_my_customer_statement", values)

    @http.route(['/my/supplier'], type='http', auth="user", website=True)
    def supplier_my_statements(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        partner = request.env['res.partner']
        partners = request.env.user.partner_id
        supplier_rfq_count = len(request.env.user.partner_id.supplier_invoice_ids)
        pager = portal_pager(
            url='/my/statements',
            total=supplier_rfq_count,
            page=page,
            step=self._items_per_page
        )
        supplier_rfq = request.env.user.partner_id.supplier_invoice_ids
        partners_data = supplier_rfq
        values = {
            'date': date_begin,
            'page_name': 'partners_data',
            'partners_data': partners_data,
            'partners': partners,
            'default_url': '/my/statements',
            'pager': pager,
        }

        return request.render("bi_customer_overdue_statement.portal_my_supplier_statement", values)

    @http.route(['/customer_portal/send_report'], type='http', auth='user', website=True)
    def send_customer_report(self, access_token=None):
        partner = request.env.user.partner_id
        partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
        if not partners_to_email and partner.email:
            partners_to_email = [partner]
        if partners_to_email:
            for partner_to_email in partners_to_email:
                mail_template_id = request.env.ref('bi_customer_overdue_statement.email_template_customer_statement')
        mail_template_id.sudo().send_mail(partner_to_email.id)
        return request.render("bi_customer_overdue_statement.send_mail_success_page")

    @http.route(['/customer_portal/download_pdf'], type='http', auth='user')
    def download_customer_report(self, access_token=None):

        reportname = 'bi_customer_overdue_statement.report_customer'

        report = request.env['ir.actions.report'].sudo()._get_report_from_name(reportname)
        partner = request.env.user.partner_id
        print("\n\nissue when reneder")
        pdf = report._render_qweb_pdf(partner.id)[0]
        print("datesteasasfa")
        report_name = 'Customer Statement' + '.pdf'
        return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'),
                                                   ('Content-Disposition', content_disposition(report_name))])

    @http.route(['/supplier_portal/send_report'], type='http', auth='user', website=True)
    def send_supplier_report(self, access_token=None):
        partner = request.env.user.partner_id
        partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
        if not partners_to_email and partner.email:
            partners_to_email = [partner]
        if partners_to_email:
            for partner_to_email in partners_to_email:
                mail_template_id = request.env.ref('bi_customer_overdue_statement.email_template_supplier_statement')
        mail_template_id.sudo().send_mail(partner_to_email.id)
        return request.render("bi_customer_overdue_statement.send_mail_success_page")

    @http.route(['/supplier_portal/download_pdf'], type='http', auth='user')
    def download_supplier_report(self, access_token=None):
        reportname = 'bi_customer_overdue_statement.report_supplier'
        report = request.env['ir.actions.report'].sudo()._get_report_from_name(reportname)
        partner = request.env.user.partner_id
        pdf = report._render_qweb_pdf(partner.id)[0]
        report_name = 'Supplier Statement' + '.pdf'
        return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'),
                                                   ('Content-Disposition', content_disposition(report_name))])
