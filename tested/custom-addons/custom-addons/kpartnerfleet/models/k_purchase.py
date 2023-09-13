import phonenumbers
from time import sleep
from tracemalloc import start
import http.client
import json
import logging
import requests
from odoo import models, api, fields
from odoo.exceptions import UserError


# update the purchase.order model to show hold a reference to a kpurchase
class KPurchaseOrder(models.Model):
    _inherit = "purchase.order"
    kpurchase_id = fields.Many2one("purchase.kpurchase")


# update the purchase.order model to show hold a reference to a kpurchase
class KPurchaseOrder(models.Model):
    _inherit = "sale.order"
    kpurchase_id = fields.Many2one("purchase.kpurchase")


# update invoice/ account.move to add a link to kpurchase
class KPurchaseOrder(models.Model):
    _inherit = "account.move"
    kpurchase_id = fields.Char("LPO Number")
    should_print_invoice = fields.Boolean('Should Print')
    location_id = fields.Many2one("partner.location", string="Location")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicles")


class KPurchase(models.Model):
    _name = "purchase.kpurchase"
    _description = "Purchase Order"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = ' id desc'

    url = '/api/2.0/advanced/transactional'
    headers = {
        'Content-type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        "application_id": "29155",
        "application_token": "jt8rfflOCsw0zyzUxwiziZYOSAREywF50U2JgZYc6hJK8l8293",
        "application_product": "http-advanced",
        "number": '',
        "text": "Vehicle: variables[vehicle],Tonnage: variables[tonnage],"
                " Location: variables[location],Purchase Order (ref: variables[name])",
        "variables": {},
        "country": "Kenya",
        "channel": {
            "sms": {
                "sender_id": "gMobile",
                "sender_id_value": "985SQEL78D",
                "unicode": True,
                "text": ''}}
    }

    start_id = 100000

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'LPO Sent'),
        ('collected', 'To Approve Collection'),
        ('approved', 'Approved'),
        ('invoiced', 'Invoiced/Billed'),
        ('paid', 'Paid'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    name = fields.Char(compute="_compute_lpo", readonly=True, store=True)

    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    vehicle_id = fields.Many2one("fleet.vehicle", required=True)
    driver_id = fields.Many2one('res.partner', 'Driver', tracking=True, help='Driver address of the vehicle',
                                copy=False)

    should_print_invoice = fields.Boolean('Print Invoice/Bill', default=True)
    supplier = fields.Many2one("res.partner", required=True)
    product = fields.Many2one("product.product", required=True)
    quantity = fields.Float("Quantity", default="1.00", required=True)
    location_id = fields.Many2one("partner.location", string="Location", required=True)
    tonnage = fields.Char(string="Tonnage", default="0.00", readonly=True, store=True, required=True)

    sale_price = fields.Float(string="Sale price", compute="_set_cost", readonly=False, store=True)
    cost_price = fields.Float(string="Cost price", compute="_set_cost", readonly=False, store=True)

    total_sale_price = fields.Float(string="Total Sale price", compute='sum', store=True)
    total_cost_price = fields.Float(string="Total Cost price", compute='sum', store=True)

    purchase_order_id = fields.Many2one('purchase.order', string="View Purchase Order", readonly=True)
    sale_order_id = fields.Many2one('sale.order', string="View Sale Order", readonly=True)
    invoice_id = fields.Many2one('account.move', string="View Sale Order", readonly=True)
    bill_id = fields.Many2one('account.move', string="View Sale Order", readonly=True)
    collected = fields.Boolean("Collected")
    invoice_paid = fields.Boolean(compute='_set_invoice_payment_status', store=True)
    bill_paid = fields.Boolean(compute='_set_bill_payment_status', store=True)
    emailed = fields.Boolean()
    sms = fields.Boolean()
    phone = fields.Char()

    @api.onchange('supplier')
    def _reset_locations(self):
        for record in self:
            record.location_id = False

    @api.onchange('partner_id')
    def _reset_vehicle(self):
        for record in self:
            record.vehicle_id = False

    @api.depends('partner_id')
    def _compute_lpo(self):
        for record in self:
            if type(record.id) == int:
                record.name = "LPO " + str(record.id + self.start_id)

    @api.onchange('quantity', 'product')
    def _compute_tonnage(self):
        for record in self:
            if record.product:
                if record.product.weight:
                    if record.product.uom_id.name == 'kg':
                        record.tonnage = str(record.product.weight * record.quantity / 1000)
                    elif record.product.uom_id.name == 'g':
                        record.tonnage = str(record.product.weight * record.quantity / 1000000)
                    else:
                        record.tonnage = str(record.product.weight * record.quantity)

    @api.onchange('product')
    def _set_cost(self):
        for record in self:
            record.cost_price = record.product.standard_price
            record.sale_price = record.product.list_price

    @api.onchange('product', 'quantity', 'cost_price', 'sale_price')
    def sum(self):
        for record in self:
            record.total_cost_price = record.cost_price * record.quantity
            record.total_sale_price = record.sale_price * record.quantity

    @api.depends('bill_id.payment_state')
    def _set_bill_payment_status(self):
        fully_paid = True
        paid = False
        for record in self:
            for invoice in record.get_bill_id():
                paid = invoice.payment_state == 'paid'
                fully_paid = fully_paid and paid
            if fully_paid and paid:
                record.bill_paid = True
            else:
                record.bill_paid = False
            self.set_paid()

    @api.depends('invoice_id.payment_state')
    def _set_invoice_payment_status(self):
        fully_paid = True
        paid = False
        for record in self:
            for invoice in record.get_invoice_id():
                paid = invoice.payment_state == 'paid'
                fully_paid = fully_paid and paid

            if fully_paid and paid:
                record.invoice_paid = True
            else:
                record.invoice_paid = False
            self.set_paid()

    def print_po(self):
        return self.env.ref('kpartnerfleet.report_kpurchase_quotation').report_action(self)

    def email_po(self):
        if self.ensure_one():
            self.env['mail.template'].browse(self.env.ref('kpartnerfleet.po_email_template').id).send_mail(
                self.get_id(), force_send=True)
            if self.state == 'draft':
                self.state = "sent"
            self.emailed = True

    def check_network_connection(self):
        try:
            response = requests.get("http://www.google.com", timeout=2)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while checking network connection: {e}")
            return False

    def sms_po(self):
        partner_phone_numbers = str(self.partner_id.phone).split(',')
        fleet_data = self.env['fleet.vehicle'].search_read([('partner_id', '=', self.partner_id.id)])
        driver_phone_numbers = []
        for vehicle in fleet_data:
            driver_phone_numbers.append(str(vehicle['phone']))

        phone_numbers = partner_phone_numbers + driver_phone_numbers
        if len(phone_numbers) > 0:
            for number in phone_numbers:
                phone_num = phonenumbers.parse(number, "RO")
                valid_number = phonenumbers.is_valid_number(phone_num)

                if valid_number:
                    if self.check_network_connection():
                        connection = http.client.HTTPSConnection('portal.bulkgate.com')
                        for key, value in self.payload.items():
                            if value == "number":
                                if key == '':
                                    self.payload[key] = number
                            if value == "channel":
                                if value == "sms":
                                    if value == "text":
                                        if key == '':
                                            self.payload[
                                                key] = f'Vehicle: {self.vehicle_id.name}, Tonnage: {self.tonnage}, Location: {self.location_id.name},  Purchase Order (ref: {self.name})',

                            if value == "variables":
                                if key == {}:
                                    self.payload[key] = {"vehicle": self.vehicle_id.name, "tonnage": self.tonnage,
                                                         "location": self.location_id.name, "name": self.name},
                        data = json.dumps(self.payload)
                        connection.request('POST', self.url, data, self.headers)

                    else:
                        raise UserError("No network connection")
                    self.message_post(
                        body="Message sent to %s:Supplier Name: %s,  Partner Name: %s,  Purchase Order ref: %s"
                             % (number,
                                self.supplier.name,
                                self.partner_id.name,
                                self.name,))

                else:
                    self.message_post(body="Message not sent! %s is invalid. Please enter a valid Phone Number. "
                                           % number)

    def set_approved(self):
        for record in self:
            record.create_purchase_order()
        sleep(1)
        pl = self.env['stock.picking'].search([('origin', '=', self.get_purchase_order().name)])
        # if not pl: return
        pl.action_set_quantities_to_reservation()
        pl.button_validate()
        self.create_sales_order()
        sleep(1)
        sl = self.env['stock.picking'].search([('origin', '=', self.get_sale_order().name)])
        # if not sl: return
        sl.action_set_quantities_to_reservation()
        sl.button_validate()
        # create bill and invoices
        sleep(1)

        self.get_sale_order()._create_invoices()
        self.get_purchase_order().action_create_invoice()
        # confim_invoices/bills
        self.set_invoiced()
        self.set_should_print_invoice()

    def set_collected(self):
        # get purchase order to reference
        self.collected = True
        self.state = "collected"

    @api.onchange('should_print_invoice')
    def set_should_print_invoice(self):
        for record in self:
            invoice = record.get_invoice_id()
            bill = record.get_bill_id()
            if bill:
                bill.should_print_invoice = record.should_print_invoice
            if invoice:
                invoice.should_print_invoice = record.should_print_invoice

    def get_id(self):
        if self.search_read():
            return self.search_read()[0]['id']

    def set_invoiced(self):
        for record in self:
            record.state = "invoiced"
            # confirm bill and invoice
            invoice = record.get_invoice_id()
            record.invoice_id = invoice.id
            invoice.invoice_date = fields.Datetime.now()
            invoice.action_post()
            # update invoice
            invoice.vehicle_id = record.vehicle_id
            invoice.location_id = record.location_id
            invoice.kpurchase_id = record.name

            bill = self.get_bill_id()
            self.bill_id = bill.id
            bill.invoice_date = fields.Datetime.now()
            bill.action_post()
            # update bill
            bill.vehicle_id = record.vehicle_id
            bill.location_id = record.location_id
            bill.kpurchase_id = record.name

            self.set_should_print_invoice()

    def set_paid(self):
        for record in self:
            if record.invoice_paid and record.bill_paid:
                record.state = "paid"

    def set_cancel(self):
        self.state = 'cancel'

    def undo_cancel(self):
        self.state = 'draft'

    def create_purchase_order(self):
        if not self.purchase_order_id:
            purchase_order = self.env['purchase.order']
            purchase_order.create({
                'partner_id': self.supplier.id,
                'state': 'purchase',
                'invoice_status': 'invoiced',
                'invoice_count': 1,
                'order_line': [(0, False, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_qty': self.quantity,
                    'qty_received': self.quantity,
                    'price_unit': self.cost_price
                })],
                'kpurchase_id': self.get_id(),
                'date_approve': fields.Datetime.now()

            })
            self.purchase_order_id = self.get_purchase_order().id

    def create_sales_order(self):
        if not self.sale_order_id:
            sales = self.env['sale.order']
            sales.create({
                'partner_id': self.supplier.id,
                'state': 'sale',  # sale quotation
                'invoice_status': 'invoiced',  # sale quotation
                'order_line': [(0, False, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': self.quantity,
                    'price_unit': self.sale_price,
                    'qty_delivered': self.quantity
                })],
                'kpurchase_id': self.get_id()
            })
            self.sale_order_id = self.get_sale_order().id

    def get_purchase_order(self):
        return self.env['purchase.order'].search([('kpurchase_id', '=', self.get_id())])

    def get_sale_order(self):
        return self.env['sale.order'].search([('kpurchase_id', '=', self.get_id())])

    def get_invoice_id(self):
        return self.get_sale_order().invoice_ids

    def get_bill_id(self):
        return self.get_purchase_order().invoice_ids
