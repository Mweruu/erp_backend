/** @odoo-module **/

import { Orderline } from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';


const PosLoyaltyOrderline = (Orderline) => class PosLoyaltyOrderline extends Orderline {
    set_quantity(quantity, keep_price) {
        if(quantity > 1 && this.eWalletGiftCardProgram) return;
        return super.set_quantity(...arguments);
    }
}
Registries.Model.extend(Orderline, PosLoyaltyOrderline);
