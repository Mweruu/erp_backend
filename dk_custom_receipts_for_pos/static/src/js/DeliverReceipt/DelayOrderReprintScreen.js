odoo.define('dk_custom_receipts_for_pos.RTDelReprintReceiptScreen', function(require) {
    "use strict";

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useErrorHandlers } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');
    const { nextFrame } = require('point_of_sale.utils');

    var core = require('web.core');
    var QWeb = core.qweb;
    const { onMounted, useRef, status } = owl;
    var self = this;

    const RTDelReprintReceiptScreen = (AbstractReceiptScreen) => {
        class RTDelReprintReceiptScreen extends AbstractReceiptScreen {
            someOrder = null;
            setup() {
                var self = this;
                super.setup();
                useErrorHandlers();
                this.orderReceipt = useRef('order-receipt');
                const order = self.props.delayed_picking_order; //this.currentOrder;
                this.someOrder = self.props.delayed_picking_order;
                onMounted(() => {
                    // Here, we send a task to the event loop that handles
                    // the printing of the receipt when the component is mounted.
                    // We are doing this because we want the receipt screen to be
                    // displayed regardless of what happen to the handleAutoPrint
                    // call.
                    setTimeout(async () => {
                        if (status(this) === "mounted") {
                            let images = this.orderReceipt.el.getElementsByTagName('img');
                            for (let image of images) {
                                await image.decode();
                            }

                            $('.pos-receipt-container').html(QWeb.render('RTDelOrderReceipt', {
                                receipt: self.props.delayed_picking_order,
                                logo: self.props.logo,
                                env: self.env
                            }));
                            const delayed_picking_order = self.props.delayed_picking_order
                            const receipt = self.props.delayed_picking_order
                            const logo =  self.props.logo
                            const env = self.env
                            await this.handleAutoPrint();
                        }
                    }, 0);
                });
            }
            _addNewOrder() {
                this.env.pos.add_new_order();
            }
            get orderAmountPlusTip() {
                const order = this.currentOrder;
                const orderTotalAmount = this.props.delayed_picking_order.total;
                const orderAmountStr = this.env.pos.format_currency(orderTotalAmount);
                return orderAmountStr;
            }
            get currentOrder() {
                return this.env.pos.get_order();
            }
            get nextScreen() {
                return { name: 'ProductScreen' };
            }
            whenClosing() {
                this.orderDone();
            }
            /**
             * This function is called outside the rendering call stack. This way,
             * we don't block the displaying of ReceiptScreen when it is mounted; additionally,
             * any error that can happen during the printing does not affect the rendering.
             */
            async handleAutoPrint() {
                if (this._shouldAutoPrint()) {
                    const currentOrder = this.someOrder;
                    await new Promise(resolve => setTimeout(resolve, 100));
                    await this.printReceipt();
                    if (this.someOrder === currentOrder && currentOrder._printed && this._shouldCloseImmediately()) {
                        this.whenClosing();
                    }
                }
            }
            orderDone() {
                this.env.pos.removeOrder(this.currentOrder);
                this._addNewOrder();
                const { name, props } = this.nextScreen;
                this.showScreen(name, props);
                if (this.env.pos.config.iface_customer_facing_display) {
                    this.env.pos.send_current_order_to_customer_facing_display();
                }
            }
            async printReceipt() {
                const isPrinted = await this._printReceiptCustom();
                if (isPrinted) {
                    this.someOrder._printed = true;
                }
            }
            _shouldAutoPrint() {
                return this.env.pos.config.iface_print_auto && !this.someOrder._printed;
            }
            _shouldCloseImmediately() {
                var invoiced_finalized = this.someOrder.to_invoice ? this.someOrder.finalized : true;
                return this.env.proxy.printer && this.env.pos.config.iface_print_skip_screen && invoiced_finalized;
            }

            async _printReceiptCustom() {
                var self = this;
                const delayed_picking_order = this.props.delayed_picking_order;
                if (this.env.proxy.printer) {
                    var order = this.props.delayed_picking_order
                    var data = { env: this.env,
                        logo: this.props.logo,
                        receipt: this.props.delayed_picking_order,
                        orderlines: order.orderlines,
                        paymentlines: order.orderpaymentlines
                    };
                    var receipt = QWeb.render('RTDelOrderReceipt',data);
                    const printResult = await this.env.proxy.printer.print_receipt(receipt);
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
                    return await this._printWeb();
                }
            }


        }
        RTDelReprintReceiptScreen.template = 'RTDelReprintReceiptScreen';
        return RTDelReprintReceiptScreen;
    };
    Registries.Component.addByExtending(RTDelReprintReceiptScreen, AbstractReceiptScreen);
    return RTDelReprintReceiptScreen;
});
