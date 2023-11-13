odoo.define('custom_receipts_for_pos.CustomButtonPaymentScreen', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Chrome = require('point_of_sale.Chrome');
    const { Component, useState, onWillStart, useRef, useEffect } =require('@odoo/owl');
    const { patch } = require('web.utils');

    const CustomButtonPaymentScreen = (PaymentScreen) =>
       class extends PaymentScreen {
           setup() {
               super.setup();
               useListener('click', this.IsCustomButton);
           }
           IsCustomButton() {
              // click_invoice
//              Gui.showPopup("ConfirmPopup", {
//                      title: this.env._t('Title'),
//                      body: this.env._t('Welcome to OWL(body of popup)'),
//                  });
          }

        _updateInputValue(event) {
        if(event){
//            console.log(event.target.value)
            this.currentOrder.set_order_customer_number(event.target.value);
            }
        }

         _updateColorValue(event) {
            console.log("uuuuu")
             return {
            backgroundColor:'rgb(255, 255, 0)' ? 'rgb(255, 255, 0)' : 'rgb(255, 0, 255)',
            color: 'white',
          };



//    toggleColor() {
//      this.isBlue = !this.isBlue;
//    },
//            console.log(event.target.value)
//            this.currentOrder.set_order_color(event.target.value);
//            console.log(this.currentOrder.customer_number)
        }
      };
    patch(PaymentScreen.prototype,'custom_receipts_for_pos.CustomButtonPaymentScreen',{
    async _isOrderValid(isForceValidate) {
        console.log("kkk)")
        let isOrderValid = this._super(isForceValidate)
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
        return isOrderValid;
    }
    });

    Registries.Component.extend(PaymentScreen, CustomButtonPaymentScreen);
    return CustomButtonPaymentScreen;
    });



