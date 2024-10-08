from odoo import api, fields, tools, models, _
from datetime import datetime


class RejectionReasonWizard(models.TransientModel):
    _name = 'sh.reject.reason.wizard'
    _description = "Reject reason wizard"

    name = fields.Char(string="Reason", required=True)

    def action_reject_order(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        active_obj = self.env[active_model].browse(active_id)

        if active_model == 'purchase.order':
            active_obj.write({
                'reject_reason': self.name,
                'reject_by': active_obj.env.user,
                'rejection_date': datetime.now(),
                'state': 'reject',
            })

            template_id = active_obj.env.ref(
                "dk_purchase_order_workflow.email_template_for_reject_purchase_order")

            if template_id:
                template_id.sudo().send_mail(active_obj.id, force_send=True, email_values={
                    'email_from': active_obj.env.user.email, 'email_to': active_obj.user_id.email})

            notifications = []
            if active_obj.user_id:
                notifications.append(
                    (active_obj.user_id.partner_id, 'sh_notification_info',
                     {'title': _('Notitification'),
                      'message': 'Dear User!! your Purchase order %s is rejected' % (active_obj.name)
                      }))
                active_obj.env['bus.bus']._sendmany(notifications)
        return True
