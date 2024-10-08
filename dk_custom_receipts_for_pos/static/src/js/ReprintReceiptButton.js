odoo.define('dk_custom_receipts_for_pos.CustomReprintReceiptButton', function (require) {
    "use strict";

    const ReprintReceiptButton = require('point_of_sale.ReprintReceiptButton');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    const CustomReprintReceiptButton = (ReprintReceiptButton) => class CustomReprintReceiptButton extends ReprintReceiptButton {
        setup() {
            super.setup();
            useListener('click', this._onClick);

        }
        async _onClick() {
            if (!this.props.order) return;
            if(!this.env.pos.config.is_enabled_print_on_refund) return;
            this.showScreen('ReprintReceiptScreen', { order: this.props.order });
        }

        printRefundReceipt() {
            return this.env.pos.config.is_enabled_print_on_refund;
        }

    }

    Registries.Component.extend(ReprintReceiptButton, CustomReprintReceiptButton);
    return CustomReprintReceiptButton;

});
