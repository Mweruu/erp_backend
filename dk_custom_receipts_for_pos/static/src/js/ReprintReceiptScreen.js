odoo.define('dk_custom_receipts_for_pos.CustomReprintReceiptScreen', function (require) {
    "use strict";

    const ReprintReceiptScreen = require('point_of_sale.ReprintReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const CustomReprintReceiptScreen = (ReprintReceiptScreen) => class CustomReprintReceiptScreen extends ReprintReceiptScreen {
        setup() {
            super.setup();
            this.props.order.reprinted = true;
        }
    }

    Registries.Component.extend(ReprintReceiptScreen, CustomReprintReceiptScreen);
    return CustomReprintReceiptScreen;

});
