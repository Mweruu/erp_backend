from datetime import datetime, time
from odoo import models, fields


class POSDifferenceReport(models.Model):
    _name = "pos.order.report.refunds"

    user_id = fields.Many2one('res.users')
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def action_print_refunds_report(self):
        data = []
        domain = []
        domain_user = []
        if self.date_from:
            domain += [('create_date', '>=', self.date_from)]
        if self.date_to:
            # convert to datatime
            dt = datetime.combine(self.date_to, time(hour=23, minute=59, second=59))
            domain += [('create_date', '<=', dt)]

        if self.user_id:
            domain_user += [('user_id', '=', self.user_id.id)]

        pos = self.env['pos.order'].search_read(domain_user)

        domain += [('qty', '<', 0)]
        orders = self.env['pos.order.line'].search_read(domain, order='qty desc')
        for order in orders:
            product = self.env['product.product'].search_read([('id', '=', order['product_id'][0])])[0]
            date = order['create_date']
            user = ''
            pos_no = ''

            for po in pos:
                if (po['id'] == order['order_id'][0]):
                    user = po['user_id'][1]
                    pos_no = po['pos_reference']

            if user == '' or pos_no == '':
                continue

            product_id = product['partner_ref']
            qty = order['qty']
            sale = order['price_unit']
            fixed = product['list_price']
            tot = round(sale * qty, 2)

            data.append({
                'date': date,
                'user': user,
                'pos_no': pos_no,
                'product_id': product_id,
                'qty': qty,
                'sale': sale,
                'fixed': fixed,
                'tot': tot
            }
            )

        data = {
            'records': data,
            'self': self.read()[0]
        }
        return self.env.ref('pos_sale_report.k_pos_refunds_transactions_report').report_action(self, data=data)
