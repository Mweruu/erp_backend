from ast import ExceptHandler
from odoo import models, api, fields


class PointOfSaleDailyReportLine(models.Model):
    _name = "pos.order.daily_report.line"
    report = fields.Many2one("pos.order.daily_report", readonly=True)
    salesperson = fields.Many2one('res.users', string="SalesPerson", readonly=True)
    tot = fields.Float(string="Total", readonly=True)
    date = fields.Datetime('Date', readonly=True)
    total_refunds = fields.Float(string="Total Refunds", readonly=True)
    total_margin = fields.Float(string="Total Margin(-ve)", readonly=True)

    _sql_constraints = [
        ('date_salep_unique', 'unique(salesperson,date)', 'Combination must be unique'),
    ]


class PointOfSaleDailyReport(models.Model):
    _name = "pos.order.daily_report"
    _description = "POS Sales Overview"

    name = fields.Char(compute="_get_value")

    def _get_value(self):
        for record in self:
            record.name = "POS " + str(record.date)

    pos_line = fields.One2many('pos.order.daily_report.line', 'report', string="")
    grand_total = fields.Float("Total", readonly=True)
    date = fields.Datetime('Date')
    cash_in_hand = fields.Float(string="Cash in Hand")
    total_refunds = fields.Float(string="Total Refunds", readonly=True)
    difference = fields.Float(compute="_find_difference", readonly=True)

    _sql_constraints = [
        ('date_salep_unique', 'unique(date)', 'Combination must be unique'),
    ]

    @api.onchange('cash_in_hand')
    def _find_difference(self):
        for record in self:
            record.difference = self.cash_in_hand - self.grand_total

    def update_pos(self):
        if not len(self.env['pos.order'].search_read()) > 0:
            return
        query = """
            INSERT INTO pos_order_daily_report_line(date,salesperson,tot,total_refunds)                
             SELECT 
                    date(pos_order.create_date),
                    pos_order.user_id,
                    sum(pos_order.amount_total) _sum,
                    sum(amount_return) _refunds
                FROM pos_order
                WHERE date(pos_order.create_date) = date(now())
                GROUP BY date(pos_order.create_date), pos_order.user_id
            ON CONFLICT (salesperson, date) DO UPDATE 
                SET 
                    tot = excluded.tot,
                    total_refunds =excluded.total_refunds            
        """

        self.env.cr.execute(query)

        se = """
                INSERT INTO pos_order_daily_report(grand_total, date,total_refunds)
                    SELECT sum(tot),date,sum(total_refunds) FROM pos_order_daily_report_line WHERE date IS NOT NULL GROUP BY date 
                ON CONFLICT (date) DO UPDATE 
                    SET grand_total = excluded.grand_total,
                        total_refunds = excluded.total_refunds
                ;

                UPDATE pos_order_daily_report_line pos_line
                SET report = (SELECT id FROM pos_order_daily_report 
                WHERE date = pos_line.date )             
        """

        self.env.cr.execute(se)

    # @api.model
    def update_all(self):
        self.update_pos()
        return self.env.ref('pos_sale_report.pos_daily_overview_view_action').read()[0]
