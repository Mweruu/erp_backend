/** @odoo-module **/

import models from 'point_of_sale.models';
import {Order} from 'point_of_sale.models';
import  Registries from "point_of_sale.Registries";
const CustomerNo = (Order) => class CustomerNo extends Order {
     constructor() {
     super(...arguments);
     this.customer_number = this.customer_number || null;
     this.color = this.color || null;
     this.delivered = this.delivered|| false;
     this.delay_picking = this.delay_picking|| false;
     }
     set_order_customer_number(customer_number){
     this.customer_number = customer_number
     }
     get_customer_number(){
        return this.customer_number;
    }
     set_order_color(color){
     this.color = color
     }
     //send order data to send to the server
     export_as_JSON() {
     const json = super.export_as_JSON(...arguments)
     json.customer_number = this.customer_number ;
     json.color = this.color ;
     json.delivered = this.delivered ;
     json.delay_picking = this.delay_picking ;
     return json;
     }
     init_from_JSON(json) {
     super.init_from_JSON(...arguments);
      this.customer_number = json.customer_number;
      this.color = json.color;
      this.delivered = json.delivered;
      this.delay_picking = json.delay_picking;
      }
     };
     Registries.Model.extend(Order, CustomerNo);

