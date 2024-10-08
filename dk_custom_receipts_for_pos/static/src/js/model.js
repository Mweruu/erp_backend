/** @odoo-module **/

import models from 'point_of_sale.models';
import {Order} from 'point_of_sale.models';
import  Registries from "point_of_sale.Registries";
const PosComponent = require('point_of_sale.PosComponent');

const CustomerNo = (Order) => class CustomerNo extends Order {
    constructor() {
        super(...arguments);
        this.customer_number = this.customer_number || null;
        this.color = this.color || null;
        this.delivered = this.delivered || false;
        this.delay_picking = this.delay_picking || false;
        this.reprinted = this.reprinted || false;
        this.vat_number = this.vat_number || false;

    }
    set_order_customer_number(customer_number){
        this.customer_number = customer_number
    }
    get_customer_number(){
        return this.customer_number;
    }
    set_order_vat_number(vat_number){
        this.vat_number = vat_number
    }
    get_vat_number(){
        return this.vat_number;
    }
    set_delayed_picking(){
        this.delay_picking = true;
    }
    set_order_color(color){
        this.color = color
    }
    set_delivered(){
        this.delivered = true;
    }
//send order data to send to the server
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments)
        json.customer_number = this.customer_number ;
        json.color = this.color ;
        json.delay_picking = this.delay_picking ;
        json.delivered = this.delivered ;
        json.reprinted = this.reprinted;
        json.vat_number = this.vat_number;
        return json;
    }
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.customer_number = json.customer_number;
        this.color = json.color;
        this.delay_picking = json.delay_picking;
        this.reprinted = json.reprinted;
        this.vat_number = json.vat_number;
    }
    export_for_printing() {
        var json = super.export_for_printing(...arguments);
        json.customer_number = this.customer_number;
        json.delay_picking = this.delay_picking;
        json.color = this.color;
        json.reprinted = this.reprinted;
        json.vat_number = this.vat_number || this.partner?.vat;
        return json;
    }
};
Registries.Model.extend(Order, CustomerNo);

