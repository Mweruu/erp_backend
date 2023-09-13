odoo.define('bi_pos_reorder.POSOrdersScreen', function (require) {
	'use strict';

	const POSOrdersScreen = require('pos_orders_list.POSOrdersScreen');
	const Registries = require('point_of_sale.Registries');
	const {useState} = owl.hooks;
	const {useListener} = require('web.custom_hooks');
	var { Gui } = require('point_of_sale.Gui');
	var core = require('web.core');
	var _t = core._t;

	const ReturnPOSOrdersScreen = (POSOrdersScreen) =>
		class extends POSOrdersScreen {
			constructor() {
				super(...arguments);
				useListener('click-returnOrder', this.clickReturnOrder);
			}
			
			clickReturnOrder(event){
				const date1 = new Date(event.detail.date_order);
				const date2 = new Date()
				const diffTime = Math.abs(date2 - date1);
				const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
				if(diffDays > this.env.pos.config.max_day_refund){
					Gui.showPopup('ErrorPopup', {
                        title: _t('Not Refund/Return Order'),
                        body: _t('Refund/Return order Time limit over...'),
                    });
                    return false;
				}
				let self = this;
				let order = event.detail;
				let o_id = parseInt(event.detail.id);
				let orderlines =  self.orderlines;				
				let pos_lines = [];

				for(let n=0; n < orderlines.length; n++){
					if (orderlines[n]['order_id'][0] ==o_id){
						pos_lines.push(orderlines[n])
					}
				}
				self.showPopup('ReturnOrderPopup', {
					'order': event.detail, 
					'orderlines':pos_lines,
				});
			}
		}
		
	Registries.Component.extend(POSOrdersScreen, ReturnPOSOrdersScreen);

	return POSOrdersScreen;
});


