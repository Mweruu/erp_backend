odoo.define('dk_custom_receipts_for_pos.CustomAbstractReceipt', function (require) {
    'use strict';
    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useErrorHandlers } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');
    const { nextFrame } = require('point_of_sale.utils');
    const { onMounted, useRef, status } = owl;


    const CustomAbstractReceipt = (AbstractReceiptScreen) => class CustomAbstractReceipt extends AbstractReceiptScreen {

        async _printReceipt() {
            if (this.env.proxy.printer) {
                const printResult = await this.env.proxy.printer.print_receipt(this.orderReceipt.el.innerHTML);
                let  printTwoReceipts = false;
                if (this.currentOrder){
                    printTwoReceipts =  this.currentOrder.delay_picking || this.currentOrder.getHasRefundLines() ||
                    this.currentOrder.orderlines.some(orderline => orderline.eWalletGiftCardProgram);
                }
                let printResult2;
                if (printTwoReceipts) {
                    printResult2= await this.env.proxy.printer.print_receipt(this.orderReceipt.el.innerHTML);
                }

                if (printResult.successful && (!printTwoReceipts)) {
                    return true;
                }
                else if (printResult.successful && printTwoReceipts && printResult2.successful){
                    return true;
                }
                else {
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
                return await this._printWeb();
            }
        }

        async _printWeb() {
            try {
                const printResult = window.print();
                const printTwoReceipts = this.currentOrder.delay_picking || this.currentOrder.getHasRefundLines() ||
                this.currentOrder.orderlines.some(orderline => orderline.eWalletGiftCardProgram);
                let printResult2;
                if(printTwoReceipts){
                    printResult2 = window.print();
                }
                if (printResult && (!printTwoReceipts)) {
                    return true;
                }
                else if (printResult && printResult2){
                    return true;
                }
            } catch (_err) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Printing is not supported on some browsers'),
                    body: this.env._t(
                        'Printing is not supported on some browsers due to no default printing protocol ' +
                        'is available. It is possible to print your tickets by making use of an IoT Box.'
                    ),
                });
                return false;
            }
        }
    };

    Registries.Component.extend(AbstractReceiptScreen, CustomAbstractReceipt);

    return CustomAbstractReceipt;
});

