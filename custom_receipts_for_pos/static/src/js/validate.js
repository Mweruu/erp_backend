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
var _t = core._t;

const PosValidateShipLaterOrder = (Order) =>
    class PosValidateShipLaterOrder extends Order{
    setup(){}

    async _validateOrder(pos_reference) {
        try{
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
                console.log("Please enter a valid Receipt Number");
            }else{
                const pickings = await rpc.query({
                model: 'stock.picking',
                method: 'search',
                args: [[['pos_order_id', '=', order[0]]]],
            });
                if (pickings.length === 0) {
                    Gui.showPopup('ErrorPopup',{
                    'title': _t('Error'),
                    'body':  _t('No matching stock picking found.'),
                    });
                    console.log("No matching stock picking found");
                } else {
                    const pickingId = pickings[0]
                    const picking = await rpc.query({
                        model: 'stock.picking',
                        method: 'read',
                        args: [pickingId, ['state']],
                    });
                    console.log("pickings", pickings[0],picking[0].state)
                    if (picking[0].state === 'assigned'){
                        console.log("validate this",this)
//                        Order 00017-014-0013
                        const result = await this.pos.env.services.rpc({
                        model: 'stock.picking',
                        method: 'button_validate_from_pos',
                        args: [pickings[0]],
                        })
                        console.log("button_validate result", result);
                        return true
                    }if (picking[0].state === 'done'){
                        Gui.showPopup('ErrorPopup',{
                        'title': _t('Error'),
                        'body':  _t('The selected order is already validated.'),
                        });
                    }
//                    else{
//                         Gui.showPopup('ErrorPopup',{
//                        'title': _t('Error'),
//                        'body':  _t('The selected order could not be validated.'),
//                        });
//                    }
                }
            }
        } catch(error){
                Gui.showPopup('ErrorPopup',{
                'title': _t('Error'),
                'body':  _t('Error validating order.'),
                });
                console.error("Error:", error);
        }
    }

    async validateOrder(pos_reference) {
        console.log("got here validateOrder")
        const res = await this._validateOrder(pos_reference);
        console.log("response = ",res)
        if (res === true) {
            console.log("Order validated successfully");
            Gui.showPopup('ConfirmPopup',{
                'title': _t('Success'),
                'body':  _t('Order validated successfully.'),
            });
        }
    }
}
Registries.Model.extend(Order, PosValidateShipLaterOrder);