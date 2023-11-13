/** @odoo-module **/

import { Order, Orderline, PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';
import session from 'web.session';
import concurrency from 'web.concurrency';
import { Gui } from 'point_of_sale.Gui';
import { round_decimals,round_precision } from 'web.utils';
import core from 'web.core';
import { Domain, InvalidDomainError } from '@web/core/domain';
import { sprintf } from '@web/core/utils/strings';


const PosValidateShipLaterOrder = (Order) => class PosValidateShipLaterOrder extends Order{
    async _validateOrder(pos_reference) {

        console.log("1got here",session.user_context)
        console.log("pos_reference",pos_reference)
        console.log("get_ship_later_orders")
        const ewe = this.pos.env.services.rpc({
        	model: 'pos.order',
        	method: 'get_ship_later_orders',
    	})
        console.log("ewe",ewe)
//    	.then(function (result) {
//        	self.do_action(result);
//    	});
        console.log("this.env.pos", "this.pos.env" ,this.pos.env.services.rpc)
//        if(pos_reference !== ){}
            const { successful, payload } = await this.pos.env.services.rpc({
                model: 'stock.picking.type',
                method: 'button_validate',
                args: [
                    [this.pos.config.id],
                ],
                kwargs: { context: session.user_context },
            });;
            if (successful) {
                console.log("got here")
            } else {
                return payload.error_message;
            }
        return true;
    }
    async validateOrder(pos_reference) {
        console.log("got here")
        const res = await this._validateOrder(pos_reference);
        if (res !== true) {
            Gui.showNotification(res);
        }
    }

}
Registries.Model.extend(Order, PosValidateShipLaterOrder);