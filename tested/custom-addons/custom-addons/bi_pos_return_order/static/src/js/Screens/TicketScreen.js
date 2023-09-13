odoo.define('bi_pos_return_order.TicketScreen', function(require) {
    'use strict';

    var { Gui } = require('point_of_sale.Gui');
    var core = require('web.core');
    var _t = core._t;

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const { patch } = require('web.utils');
    const session = require('web.session');
//    const summary = require('point_of_sale.OrderSummary');

    const RefundTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            async _onDoRefund() {
                        console.log(userId, session.user_context);

                const order = this.getSelectedSyncedOrder();
                const date1 = new Date(order.validation_date);
                const date2 = new Date()
                const diffTime = Math.abs(date2 - date1);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                if(diffDays > this.env.pos.config.max_day_refund){
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Not Refund/Return Order'),
                        body: _t('Refund/Return order Time limit over...'),
                    });
                    return false;
                }
                await super._onDoRefund();
            }
            _getFilterOptions() {
                const orderStates = this._getOrderStates();
                if(this.env.pos.config.is_enabled_refund){
                    orderStates.set('SYNCED', { text: this.env._t('Paid') });
                }
                return orderStates;
            }
        };

        patch(TicketScreen.prototype,'bi_pos_return_order.TicketScreen',{
        getFilteredOrderList() {
           let filteredOrders = this._super()
            if(this.env.pos.config.is_show_all_orders ){
                console.log(this.env.pos.config.orders, this.env.orders, this.env.pos.config.name,this.env.pos.config.is_show_all_orders, session);
                const userId = session.user_context.uid;
                console.log(userId, session.user_context);
                filteredOrders = filteredOrders.filter(order => order.user_id === userId);
//                if (this.env.pos.config.orders )return this._state.syncedOrders.toShow
//                filteredOrders =
//                this.env.pos.config.orders = this._state.syncedOrders.toShow
//                const predicate = (order) => {
//                return filterCheck(order) && searchCheck(order);
//                };
//                console.log(this.env.pos.config.orders, filteredOrders)
//                return this.env.pos.config.orders.filter(predicate)
                return filteredOrders;
            }
            console.log(this.env.pos.config.is_show_all_orders, this.env.pos.config.name, session);
            return filteredOrders;
        }
        });
    Registries.Component.extend(TicketScreen, RefundTicketScreen);

    return RefundTicketScreen;

});