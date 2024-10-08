odoo.define('dk_custom_receipts_for_pos.HidePromoCodeButton', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const HidePromoCodeButton = Registries.Component.get('PromoCodeButton');
    ProductScreen.addControlButton({
        component: HidePromoCodeButton,
        condition: function () {
            return this.env.pos.config.view_enter_code;
        },
        position: ['replace', 'PromoCodeButton'],

    });

});

