odoo.define('dk_custom_receipts_for_pos.DeliverButton', function(require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    class DeliverButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {
            let { confirmed, payload: pos_reference} = await this.showPopup("TextInputPopup", {
                title: this.env._t('Enter Receipt Number'),
                startingValue: '',
                placeholder: this.env._t('Receipt Number'),
            });
            if (confirmed) {
                pos_reference = pos_reference.trim();
                const validFormatPattern = /^\d{5}-\d{3}-\d{4}$/;
                if (validFormatPattern.test(pos_reference) ) {
                    await this.env.pos.get_order().validateOrder(pos_reference);
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

    DeliverButton.template = 'DeliverButton';

    ProductScreen.addControlButton({
        component: DeliverButton,
        condition: function() {
            return this.env.pos.config.ship_later;
        },
    });

    Registries.Component.add(DeliverButton);

    return DeliverButton;
});