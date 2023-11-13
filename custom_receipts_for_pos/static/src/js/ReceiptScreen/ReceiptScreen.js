odoo.define('custom_receipts_for_pos.CustomReceiptScreen', function (require) {
    'use strict';

    const { nextFrame } = require('point_of_sale.utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');
    const { useRef } = owl;
    const { patch } = require('web.utils');


    patch(AbstractReceiptScreen.prototype,'custom_receipts_for_pos.CustomReceiptScreen',{
    async _printReceipt() {
        console.log(1)
        let printNotShipLaterReceipt = this._super();
        if(this.currentOrder.is_to_ship()){
            console.log(2)
            if (this.env.proxy.printer) {
                const printResult = await this.env.proxy.printer.print_receipt(this.orderReceipt.el.innerHTML);
                if (printResult.successful) {
                    return true;
                } else {
                    await this.showPopup('ErrorPopup', {
                        title: printResult.message.title,
                        body: printResult.message.body,
                    });
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: printResult.message.title,
                        body: this.env._t('Do you want to print using the web printer?'),
                    });
                    if (confirmed) {
                        // We want to call the _printWeb when the popup is fully gone
                        // from the screen which happens after the next animation frame.
                        await nextFrame();
                        return await this._printWeb();
                    }
                    return false;
                }
            } else {
                console.log("gothere",898789)
                return await this._printWeb();
            }
        }
        return printNotShipLaterReceipt

        }
        });

        });
