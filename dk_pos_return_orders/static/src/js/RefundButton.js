odoo.define('dk_pos_return_orders.ExtendRefundButton', function (require) {
    'use strict';

    const RefundButton = require('point_of_sale.RefundButton');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    const { patch } = require('web.utils');

    const ExtendRefundButton = (RefundButton) => class extends RefundButton {
        async _onClick() {
            let { confirmed, payload: pos_reference} = await this.showPopup("TextInputPopup", {
                title: this.env._t('Enter Receipt Number'),
                startingValue: '',
                placeholder: this.env._t('Receipt Number'),
            });
            if (confirmed) {
                pos_reference = pos_reference.trim();
                const validFormatPattern = /^\d{5}-\d{3}-\d{4}$/;

                if (validFormatPattern.test(pos_reference) ) {
                    this.env.pos.get_order().refundOrder(pos_reference).then((result) => {
                        const searchDetails = { fieldName: 'RECEIPT_NUMBER', searchTerm: pos_reference };
                        if(result){
                            this.showScreen('TicketScreen',{
                                ui: { filter: 'SYNCED', searchDetails },
                            })
                        }
                    })
                }
                else
                {
                    this.showPopup('ErrorPopup',{
                        title: this.env._t('Invalid format'),
                        body:  this.env._t('Please enter a Receipt Number in the format 00000-000-0000.'),
                    });
                }
            }
        }

    }

    const HideRefundButton = Registries.Component.get('RefundButton');
    ProductScreen.addControlButton({
        component: HideRefundButton,
        condition: function() {return this.env.pos.config.is_enabled_refund},
        position: ['replace', 'RefundButton'],
    });

    Registries.Component.extend(RefundButton, ExtendRefundButton);

    return ExtendRefundButton;
});
