odoo.define('dk_custom_receipts_for_pos.CustomButtonPaymentScreen', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Chrome = require('point_of_sale.Chrome');
    const { Component, useState, onWillStart, useRef, useEffect } = require('@odoo/owl');

    const CustomButtonPaymentScreen = (PaymentScreen) => class extends PaymentScreen {
        setup() {
            super.setup();
        }

        _updateInputValue(event) {
            if(event){
                this.currentOrder.set_order_customer_number(event.target.value);
            }
        }
        _updateVATInputValue(event) {
            if(event){
                event.target.value = event.target.value.toUpperCase().trim()
                this.currentOrder.set_order_vat_number(event.target.value);
            }
        }

        toggleChangeColour(ev){
            if (ev && ev.target) {
                if($(ev.target).hasClass('colours-selection-blue')){
                    $(ev.target).removeClass('colours-selection-blue');
                    $(ev.target).addClass('colours-selection-yellow');
                    $(ev.target).find("i.fa").removeClass('fa-flag-o');
                    $(ev.target).find("i.fa").addClass('fa-flag');
                }
                else{
                    $(ev.target).removeClass('colours-selection-yellow');
                    $(ev.target).addClass('colours-selection-blue');
                    $(ev.target).find("i.fa").removeClass('fa-flag');
                    $(ev.target).find("i.fa").addClass('fa-flag-o');
                }
            }
        }

        isPriceAllowed(list_price, price){
            const difference = list_price - price;
            const absolutepercentage = Math.abs(difference/list_price * 100);
            return absolutepercentage < this.env.pos.config.set_percentage_range;
        }

        async _isOrderValid(isForceValidate) {
            let isOrderValid = await super._isOrderValid(isForceValidate)
            var number = '';
            var error = false;
            let invalidPrices = false;
            if($("[name='customer_number']").length == 1){
                number = $("[name='customer_number']").val().trim();
            }
            if (this.currentOrder.is_to_ship()){
                this.currentOrder.set_delayed_picking();
            }
            else {
                this.currentOrder.set_delivered();
            }
            if(this.currentOrder.orderlines.some(orderline => orderline.quantity == 0)){
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Zero Quantity'),
                    body: this.env._t(
                        'Quantity on an orderline cannot be zero'
                    ),
                });
                return;
            }
            if(this.env.pos.config.set_percentage_range_bool){
                for (const orderLine of this.currentOrder.orderlines){
                    if (!orderLine.eWalletGiftCardProgram && !this.isPriceAllowed(orderLine.product.lst_price, orderLine.price )){
                        invalidPrices = true;
                        break;
                    }
                }
            }
            if (invalidPrices){
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Invalid Selling Price'),
                    body: this.env._t(
                        'The Selling Price is not correct'
                    ),
                });
                return;
            }
            if (this.currentOrder.customer_number){
                const kenyanPhoneRegex = /^[0-9]{10}$/;
                if (!kenyanPhoneRegex.test(this.currentOrder.customer_number)) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Invalid phone number'),
                        body: this.env._t(
                            'You need to enter a valid phone number before you can validate an order.'
                        ),
                    });
                    return;
                } else {
                    console.log("Valid Kenyan Phone Number");
                }
            }
            if (this.currentOrder.vat_number && !this.currentOrder.partner){
                const vatNumberRegex = /^[A-Z]{1}[0-9]{9}[a-zA-Z]{1}$/;
                if (!vatNumberRegex.test(this.currentOrder.vat_number)) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Invalid PIN number'),
                        body: this.env._t(
                            'You need to enter a valid PIN number before you can validate an order.'
                        ),
                    });
                    return;
                } else {
                    console.log("Valid PIN Number");
                }
            }
            if ((this.currentOrder.is_to_ship()) && !this.currentOrder.get_customer_number()) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Please enter a valid phone number'),
                    body: this.env._t(
                        'You need to enter a valid phone number before you can validate an order.'
                    ),
                });
                if (confirmed) {
                    this._updateInputValue();
                }
                return false;
            }
            if ($(".change-color-button").hasClass('colours-selection-blue')){
                this.currentOrder.set_order_color('blue');
            }else if ($(".change-color-button").hasClass('colours-selection-yellow')){
                this.currentOrder.set_order_color('yellow');
            }
            if (error){
                return false;
            }
            else{
                return isOrderValid;
            }
        }
    }
    Registries.Component.extend(PaymentScreen, CustomButtonPaymentScreen);
    return CustomButtonPaymentScreen;
});



