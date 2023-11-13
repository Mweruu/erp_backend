from odoo import fields, models


class YWTPurchaseOrderAutomationHistory(models.Model):
    _name = 'ywt.purchase.order.automation.history'
    _description = "Purchase Order Automation History"  
     
    name = fields.Char(string="Name") 
    mismatch_type = fields.Selection([('purchase', 'Purchase'), ('transfer', 'Transfer'), ('invoice', 'Invoice')], string="Mismatch Type")
    error_message = fields.Text(string="Error Message")
    
    def create_purchase_order_automation_history(self):
        sequence_id = self.env.ref('od_purchase_order_workflow.ywt_purchase_automation_history_sequence').ids
        if sequence_id:
            record_name = self.env['ir.sequence'].get_id(sequence_id[0])
        else:
            record_name = '/'
        history_vals = {'name': record_name}
        purchase_order_automation_history_id = self.create(history_vals)
        return purchase_order_automation_history_id
