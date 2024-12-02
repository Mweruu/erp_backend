odoo.define('dk_pos_return_orders.TicketScreen', function(require) {
    'use strict';

    var { Gui } = require('point_of_sale.Gui');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const { patch } = require('web.utils');
    const session = require('web.session');
    const models = require('point_of_sale.models');
    const { Order } = require('point_of_sale.models');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { useListener } = require("@web/core/utils/hooks");

    const RefundTicketScreen = (TicketScreen) =>
    class extends TicketScreen {

        setup() {
            super.setup();
            useListener('do-refund-all', this._onRefundAllButtonClick);
        }

        async _fetchSyncedOrders() {
            if(this.env.pos.config.is_show_all_orders){
                const config = JSON.parse(this.env.pos.config.all_config_id)
                const domain = this._computeSyncedOrdersDomain();
                const limit = this._state.syncedOrders.nPerPage;
                const offset = (this._state.syncedOrders.currentPage - 1) * this._state.syncedOrders.nPerPage;
                const { ids, totalCount } = await this.rpc({
                    model: 'pos.order',
                    method: 'search_paid_order_ids',
                    kwargs: { config_id: config, domain, limit, offset },
                    context: this.env.session.user_context,
                });
                const idsNotInCache = ids.filter((id) => !(id in this._state.syncedOrders.cache));
                if (idsNotInCache.length > 0) {
                    const fetchedOrders = await this.rpc({
                        model: 'pos.order',
                        method: 'export_for_ui',
                        args: [idsNotInCache],
                        context: this.env.session.user_context,
                    });
                    // Check for missing products and partners and load them in the PoS
                    await this.env.pos._loadMissingProducts(fetchedOrders);
                    await this.env.pos._loadMissingPartners(fetchedOrders);
                    // Cache these fetched orders so that next time, no need to fetch
                    // them again, unless invalidated. See `_onInvoiceOrder`.
                    fetchedOrders.forEach((order) => {
                        this._state.syncedOrders.cache[order.id] = Order.create({}, { pos: this.env.pos, json: order });
                    });
                }
                this._state.syncedOrders.totalCount = totalCount;
                this._state.syncedOrders.toShow = ids.map((id) => this._state.syncedOrders.cache[id]);
            }
            else
            {
                super._fetchSyncedOrders();
            }
        }

        async _onDoRefund() {
            if(this.env.pos.config.is_enabled_refund){
                super._onDoRefund();
            }else{
                return;
            }
        }

        _getFilterOptions() {
            super._getFilterOptions()
            const orderStates = this._getOrderStates();
            if(this.env.pos.user.role === 'manager'|| this.env.pos.config.is_enabled_refund){
                orderStates.set('SYNCED', { text: this.env._t('Paid') });
            }
            return orderStates;
        }

        _onUpdateSelectedOrderline({ detail }) {
            const order = this.getSelectedSyncedOrder();
            const selectedOrderlineId = this.getSelectedOrderlineId();
            const orderline = order.orderlines.find((line) => line.id == selectedOrderlineId);
            const currentOrder = this.env.pos.get_order();
            currentOrder.vat_number = order.partner?.vat ?? order.vat_number;
            currentOrder.customer_number = order.partner?.phone ?? order.customer_number;
            if (!this.env.pos.config.is_enabled_refund || orderline.is_reward_line){
                this._showNotAllowedRefundProductNotification();
                return NumberBuffer.reset();
            }
            var self = this;
            if (!order) return NumberBuffer.reset();
            const res = super._onUpdateSelectedOrderline({detail});
            if (!orderline) return NumberBuffer.reset();
            const toRefundDetail = this._getToRefundDetail(orderline);
            if (toRefundDetail.destinationOrderUid) return NumberBuffer.reset();
            let return_products = {};
            rpc.query({
                model: 'pos.order',
                method: 'search_read',
                args: [[['id', '=', order.backendId]]],
            }).then(function (refunds){
                if(!refunds[0].delivered){
                    Gui.showPopup('ErrorPopup',{
                        'title': _t('Undelivered Order'),
                        'body':  _t('The selected Order has not been delivered.'),
                    });
                    toRefundDetail.qty = 0;
                    return false;
                }
                const date1 = new Date(refunds[0].pos_order_date);
                const date2 = new Date()
                const diffTime = Math.abs(date2 - date1);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                if(diffDays > self.env.pos.config.max_day_refund){
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Not Refund/Return Order'),
                        body: _t('Refund/Return order Time limit over...'),
                    });
                    toRefundDetail.qty = 0;
                    return false;
                }
                return true;
            });
            return res;
        }

        _onRefundAllButtonClick() {
            var self = this;
            const order = this.getSelectedSyncedOrder();
            if (!order) return NumberBuffer.reset();

            const selectedOrderlineId = this.getSelectedOrderlineId();
            const orderline = order.orderlines.find((line) => line.id == selectedOrderlineId);
            if (!orderline) return NumberBuffer.reset();

            const currentOrder = this.env.pos.get_order();
            currentOrder.vat_number = order.partner?.vat ?? order.vat_number;
            currentOrder.customer_number = order.partner?.phone ?? order.customer_number;

            rpc.query({
                model: 'pos.order',
                method: 'search_read',
                args: [[['id', '=', order.backendId]]],
            }).then(function(refunds) {
                if (!refunds[0].delivered) {
                    Gui.showPopup('ErrorPopup', {
                        'title': _t('Undelivered Order'),
                        'body': _t('The selected Order has not been delivered.'),
                    });
                    NumberBuffer.reset();
                    return false;
                }

                const date1 = new Date(refunds[0].pos_order_date);
                const date2 = new Date();
                const diffTime = Math.abs(date2 - date1);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                if (diffDays > self.env.pos.config.max_day_refund) {
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Not Refund/Return Order'),
                        body: _t('Refund/Return order Time limit over...'),
                    });
                    NumberBuffer.reset();
                    return false;
                }

                order.orderlines.forEach((orderline) => {
                    if (orderline && self._isEWalletGiftCard(orderline)) {
                        self._showNotAllowedRefundNotification();
                        return NumberBuffer.reset();
                    }

                    if (!self.env.pos.config.is_enabled_refund || !self.env.pos.config.is_enabled_refund_all || orderline.is_reward_line) {
                        self._showNotAllowedRefundProductNotification();
                        return NumberBuffer.reset();
                    }

                    const toRefundDetail = self._getToRefundDetail(orderline);

                    if (toRefundDetail.destinationOrderUid) return;

                    const refundableQty = toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
                    if (refundableQty > 0) {
                        toRefundDetail.qty = refundableQty;
                    } else {
                        NumberBuffer.reset();
                    }
                });
            });
        }

        _showNotAllowedRefundProductNotification() {
            this.showNotification(this.env._t("Refunding a product is not allowed."), 5000);
        }

    }

    Registries.Component.extend(TicketScreen, RefundTicketScreen);

    return RefundTicketScreen;
});