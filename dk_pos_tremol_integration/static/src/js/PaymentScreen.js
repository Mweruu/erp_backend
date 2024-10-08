odoo.define('dk_pos_tremol_integration.KRAIntegrationPaymentScreen', function (require) {
    'use strict';

    const { identifyError } = require('point_of_sale.utils');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const { Component } =require('@odoo/owl');
    const rpc = require('web.rpc');
    const core = require('web.core');
    const { isConnectionError } = require('point_of_sale.utils');
    const _t = core._t;


    const KRAIntegrationPaymentScreen = (PaymentScreen) => class extends PaymentScreen {

        async _finalizeValidation() {
            const sendToTIMS = this.env.pos.config.is_send_to_TIMS &&
            !this.currentOrder.orderlines.every(orderline => orderline.eWalletGiftCardProgram) &&
            !this.currentOrder.is_to_invoice();

            if(!sendToTIMS){
                this.currentOrder.manual_etr = true;
            }

            if (sendToTIMS){
                try {
                    this.env.services.ui.block()
                    const current_order = this.env.pos.orders;
                    var orders = this.currentOrder.export_as_JSON();
                    try {
                        const response = await this.env.services.rpc({
                            model: 'pos.order',
                            method: 'l10n_ke_action_cu_post',
                            args: [orders],
                        });
                        this.currentOrder.reversed_entry_id = response.params.invoices.reversed_entry_id;
                        await this.post_send_pos(response)
                    } catch (error) {
                        console.error(error)
                        if (isConnectionError(error)) {
                            throw new Error(_t('Error connecting to server. Issue a manual ETR'))
                        } else {
                            throw error;
                        }
                    }
                }
                catch (error){
                    this.currentOrder.manual_etr = true;
                    let errorMessage = error.message && error.message.data && error.message.data.message;
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error.'),
                        body: errorMessage ? errorMessage : error.message
                    });
                }
                finally {
                    this.env.services.ui.unblock()
                }
            }
            return super._finalizeValidation()
        }

    }
    Registries.Component.extend(PaymentScreen, KRAIntegrationPaymentScreen);
    return KRAIntegrationPaymentScreen;
});