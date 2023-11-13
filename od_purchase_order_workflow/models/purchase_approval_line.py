from odoo import api, fields, tools, models, _

class PurchaseApprovalLine(models.Model):
    _name = 'sh.purchase.approval.line'
    _description = 'Dynamic Purchase Approval'

    from_amount = fields.Float(string="From Amount",required=True,)
    to_amount = fields.Float(string="To Amount",required=True)
    level=fields.Integer(string="Level",required=True)
    approve_by = fields.Selection(
        [('group','Group'),('user','User')],string="Approve Process By",default="user",required=True,)
    user_ids = fields.Many2many('res.users', string="Users")
    group_ids = fields.Many2many('res.groups', string="Groups")
    purchase_approval_config_id=fields.Many2one('sh.purchase.approval.config')
    is_boolean=fields.Boolean()

    @api.onchange('approve_by')
    def onchange_approve_by(self):
        
        if self.approve_by=='user':
            self.is_boolean=False
        if self.approve_by=='group':
            self.is_boolean=True
        