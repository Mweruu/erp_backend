odoo.define('dk_pos_return_orders.PosRefundOrder', function(require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const { Order, Orderline, PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { isConnectionError } = require('point_of_sale.utils');

    var core = require("web.core");
    var rpc = require('web.rpc');
    var _t = core._t;

    const PosRefundOrder = (Order) =>
    class PosRefundOrder extends Order{
        setup(){
            super.setup();
        }

        async refundOrder(pos_reference) {
            try{
                const order = await this.pos.env.services.rpc({
                    model: 'pos.order',
                    method: 'search',
                    args: [[['pos_reference', 'in', ['Order ' + pos_reference]]]],
                });
                if (order.length === 0) {
                    Gui.showPopup('ErrorPopup',{
                        'title': _t('Error'),
                        'body':  _t('Please enter a valid Receipt Number.'),
                    });
                    return false;
                }
                else
                {
                    const orderRefund = order[0]
                    const orderState = await this.pos.env.services.rpc({
                        model: 'pos.order',
                        method: 'read',
                        args: [orderRefund, ['delivered']],
                    });
                    if (!orderState[0].delivered){
                        Gui.showPopup('ErrorPopup',{
                            'title': _t('Undelivered Order'),
                            'body':  _t('The selected Order has not been delivered.'),
                        });
                        return false;
                    }
                    else
                    {
                        return true;
                    }
                }
            } catch(error){
                console.error('Error while making the RPC call:', error);
                let errorMessage = error.message ? error.message : ''
                if (isConnectionError(error)) {
                    errorMessage = errorMessage + '. ' +  'Network Failure, Please check your internet connection'
                } else {
                    errorMessage = errorMessage + '. ' +  'Error returning order.'
                }
                Gui.showPopup('ErrorPopup',{
                    'title': _t('Error'),
                    'body':  _t(errorMessage),
                });
                return false;
            }
        }

    }
    Registries.Model.extend(Order,PosRefundOrder);
    return PosRefundOrder;

});
