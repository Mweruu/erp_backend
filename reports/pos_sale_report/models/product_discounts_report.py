import base64
import csv
import io

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ProductDiscountsReport(models.Model):
    _name = 'product.discounts.report'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    list_base_price = fields.Float(string='Sale Base Price', digits='Product Price', required=True, default=0.0)

    def get_product_discounts_report_data(self):
        data = []

        discounts = self.env['product.template'].search([('list_base_price', '>', 0)])

        for discount in discounts:
            product_id = discount['name']
            q1 = discount['list_price']
            q2 = discount['new_standard_price']
            diff = round((float(q1)) - (float(q2)), 2)
            logger.debug(f"q1: {q1}, q2:{q2},Difference: {diff}")
            if product_id:
                data.append({
                    'Product Name': discount['name'],
                    'Sales Price': discount['list_price'],
                    'Standard Price': discount['standard_price'],
                    'Sale Base Price': discount['list_base_price'],
                    'Difference': diff,
                })
        data = {
            'records': data,
            'self': self.read()[0]
        }
        return data

    def action_print_base_price_report(self):
        report_data = self.get_product_discounts_report_data()
        return self.env.ref('pos_sale_report.product_discounts_report').report_action(None, data=report_data)

    def action_print_base_price_report_csv(self):
        report_data = self.get_product_discounts_report_data()
        if not report_data['records']:
            return {
                'warning': {
                    'title': 'No Data',
                    'message': 'There is no data to export.',
                },
            }
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(report_data['records'][0].keys())
        for record in report_data['records']:
            writer.writerow(record.values())
        content = output.getvalue().encode('utf-8')
        filename = 'Base Price with variance.csv'
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id={}&filename={}&field=datas&download=true&filename={}'.format(
                self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.b64encode(content),
                    'mimetype': 'text/csv'
                }).id,
                filename,
                filename
            ),
            'target': 'new'
        }


class BasePriceReport(models.Model):
    _name = 'base.price.report'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', default=_default_user)
    list_base_price = fields.Float(string='Sale Base Price', digits='Product Price', required=True, default=0.0)

    def get_base_price_report_data(self):
        data = []

        prices = self.env['product.template'].search([('list_base_price', '=', 0)])

        for price in prices:
            q1 = price['list_price']
            q2 = price['standard_price']
            diff = round((float(q1)) - (float(q2)), 2)
            logger.debug(f"q1: {q1}, q2:{q2},Difference: {diff}")
            data.append({
                'Product Name': price['name'],
                'Sales Price': price['list_price'],
                'Standard Price': price['standard_price'],
                'Sale Base Price': price['list_base_price'],
                'Difference': diff
            })
        data = {
            'records': data,
            'self': self.read()[0]
        }
        return data

    def action_print_base_price_report(self):
        report_data = self.get_base_price_report_data()
        return self.env.ref('pos_sale_report.base_price_report').report_action(None, data=report_data)

    def action_print_base_price_report_csv(self):
        report_data = self.get_base_price_report_data()
        if not report_data['records']:
            logger.info(f"No data")
            return {
                'warning': {
                    'title': 'No Data',
                    'message': 'There is no data to export.',
                },
            }
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(report_data['records'][0].keys())
        for record in report_data['records']:
            writer.writerow(record.values())
        content = output.getvalue().encode('utf-8')
        filename = 'BasePricewithoutVariance.csv'
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id={}&filename={}&field=datas&download=true&filename={}'.format(
                self.env['ir.attachment'].create({
                    'name': filename,
                    'datas': base64.b64encode(content),
                    'mimetype': 'text/csv'
                }).id,
                filename,
                filename
            ),
            'target': 'new'
        }
