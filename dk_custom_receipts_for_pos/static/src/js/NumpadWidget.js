odoo.define('dk_custom_receipts_for_pos.CustomNumpadWidget', function (require) {
    'use strict';

    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');

    const CustomNumpadWidget = (NumpadWidget) => class CustomNumpadWidget extends NumpadWidget {
        get hasToggleSign() {
            return this.env.pos.config.toggle_sign;
        }
    }

    Registries.Component.extend(NumpadWidget, CustomNumpadWidget);

    return CustomNumpadWidget;

});