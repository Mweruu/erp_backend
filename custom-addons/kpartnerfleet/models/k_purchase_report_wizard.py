from odoo import fields, api, models

class KPurchaseReportWizard(models.TransientModel):
    _name="purchase.kpurchase.wizard"
    _description ="KPurchase Report Wizard"

    partner = fields.Many2one('res.partner', required=True, string="Partner")

    date_from =  fields.Datetime ('Date from')
    date_to = fields.Datetime ('Date to')

    def action_print_report(self):
        domain = []
        domain += [('partner_id','=', self.partner.id)]
        if self.date_from:
            domain+=[('create_date', '>=',self.date_from)]
        if self.date_to:
            domain+= [('create_date', '<=', self.date_to)]

        transactions = self.env['purchase.kpurchase'].search_read(domain, order='id')
        data={
            'form'  : self.read()[0],
            'transactions':transactions
            }

        return self.env.ref("kpartnerfleet.k_purchase_orders_transactions_report").report_action(self, data=data)

