odoo.define('custom_receipts_for_pos.DeliverButton', function(require) {
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
            console.log(this.env.pos)
//            console.log(this.env.pos.get_order())
            let { confirmed, payload: pos_reference} = await this.showPopup("TextInputPopup", {
                      title: this.env._t('Enter Receipt Number'),
                      startingValue: '',
                      placeholder: this.env._t('Receipt Number'),
                  });
                              console.log("!confirmed")
            if (confirmed) {
                console.log("confirmed")
                pos_reference = pos_reference.trim();
                if (pos_reference !== '') {
                    this.env.pos.get_order().validateOrder(pos_reference);
                }
            }
            }
    }

//custom_receipts_for_pos
    DeliverButton.template = 'DeliverButton';

    ProductScreen.addControlButton({
        component: DeliverButton,
        condition: function() {
          return this.env.pos;
//            return true;
        },
    });

    Registries.Component.add(DeliverButton);

    return DeliverButton;
})