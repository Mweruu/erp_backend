from odoo import models, fields, api, _
import logging
import random

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    has_queue_job = fields.Boolean(
        default=False,
        help="This checkbox is checked if the generation of"
             " the picking has been delayed. The picking will be created by cron.",
    )

    def _order_fields(self, ui_order):
        """ Prepare dictionary for create method """
        result = super(PosOrder, self)._order_fields(ui_order)
        result["has_queue_job"] = ui_order["has_queue_job"]
        return result

    @api.model
    def create_from_ui(self, orders, draft=False):
        PosSession = self.env["pos.session"]
        for order_data in orders:
            session_id = order_data.get("data").get("pos_session_id")
            session = PosSession.browse(session_id)
            order_data["data"][
                "has_queue_job"
            ] = session.config_id.picking_creation_delayed
        return super(PosOrder, self.with_context(create_from_ui=True)).create_from_ui(
            orders, draft=draft
        )

    #  It will be executed as soon as the Jobrunner has a free bucket,
    #  which can be instantaneous if no other job is running.
    def _create_order_picking(self):
        if self.env.context.get("create_from_ui", False):
            orders = self.filtered(lambda x: not x.has_queue_job)
            delayed_orders = self.filtered(lambda x: x.has_queue_job)
            random_number = random.randint(2, 15)
            job1 = delayed_orders.delayable(eta=(60 * random_number), max_retries=10)._create_delayed_picking()
            job2 = delayed_orders.delayable(eta=(60 * (random_number + 3)), max_retries=10)._compute_total_cost()
            job1.on_done(job2).delay()
        else:
            orders = self

        if orders:
            res = super(PosOrder, orders)._create_order_picking()
            orders.write({"has_queue_job": False})
            return res

    def _create_delayed_picking(self):
        # make the function idempotent
        _logger.info("Delayed picking starting up")
        orders = self.filtered(lambda x: x.has_queue_job)
        super(PosOrder, orders)._create_order_picking()

    def _compute_total_cost(self):
        # make the function idempotent
        orders = self.filtered(lambda x: x.has_queue_job)
        super(PosOrder, orders)._compute_total_cost_in_real_time()
        orders.write({"has_queue_job": False})
