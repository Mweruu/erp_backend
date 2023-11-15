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
var rpc = require('web.rpc');
var self = this; // Preserve the 'this' context
var _t = core._t;


const PosValidateShipLaterOrder = (Order) =>
    class PosValidateShipLaterOrder extends Order{
    setup(){}


    async _validateOrder(pos_reference) {
        try{
//    	});Order 00013-001-0001 search for picking_type_id
         const order = await rpc.query({
                model: 'pos.order',
                method: 'search',
                args: [[['pos_reference', '=', pos_reference]]],
            });
            console.log("order", order[0]);
            if (order.length === 0) {
                Gui.showPopup('ErrorPopup',{
                'title': _t('Error'),
                'body':  _t('Please enter a valid Receipt Number.'),
                });
//                    this.displayNotification({ title: _t("Error"), message: _t("Please enter a valid Receipt Number"), type: 'danger' });
                console.log("Please enter a valid Receipt Number");
            }else{
                const pickings = await rpc.query({
                model: 'stock.picking',
                method: 'search',
                args: [[['pos_order_id', '=', order[0]]]],
            });
                console.log("pickings", pickings[0]);
                if (pickings.length === 0) {
                    Gui.showPopup('ErrorPopup',{
                    'title': _t('Error'),
                    'body':  _t('No matching stock picking found.'),
                    });
                    console.log("No matching stock picking found");
//                        this.displayNotification({ title: _t("Error"), message: _t("No matching stock picking found"), type: 'danger' });
                } else {
                    const result = await this.pos.env.services.rpc({
                    model: 'stock.picking',
                    method: 'button_validate',
                    args: [
                    ],
                    });
//                                            pickings[0]Order 00013-001-0001
//                    if (successful) {
//                        console.log("got here successful")
//                    } else {
//                        console.log("got here error")
//                        return payload.error_message;
//                    }
                     console.log("button_validate result", result);
                     return result
                }
            }
        } catch(error){
                console.error("Error:", error);

        }
    }



//            const { successful, payload } = await this.pos.env.services.rpc({
//                model: 'stock.picking',
//                method: 'button_validate',
//                args: [
//                    [pickings[0]],
//                ],
//                kwargs: { context: session.user_context },
//            });;
//            if (successful) {
//                console.log("got here successful")
//            } else {
//                console.log("got here error")
//                return payload.error_message;
//            }
//        return true;

    async validateOrder(pos_reference) {
        console.log("got here validateOrder")
        const res = await this._validateOrder(pos_reference);
        if (res === true) {
            console.log("Order validated successfully");
            Gui.showPopup('ConfirmPopup',{
                'title': _t('Success'),
                'body':  _t('Order validated successfully.'),
            });
        } else {
            console.log("Error validating order");
            Gui.showPopup('ErrorPopup',{
                'title': _t('Error'),
                'body':  _t('Error validating order.'),
            });
        }
    }

}
Registries.Model.extend(Order, PosValidateShipLaterOrder);