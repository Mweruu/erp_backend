odoo.define('dk_custom_receipts_for_pos.HideSetSaleOrderButton', function (require) {
    'use strict';

    const SetSaleOrderButton = require('pos_sale.SetSaleOrderButton');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const HideSetSaleOrderButton = Registries.Component.get('SetSaleOrderButton');
    ProductScreen.addControlButton({
        component: HideSetSaleOrderButton,
        condition: function() {return this.env.pos.config.view_quotation_order},
        position: ['replace', 'SetSaleOrderButton'],
    });
});

