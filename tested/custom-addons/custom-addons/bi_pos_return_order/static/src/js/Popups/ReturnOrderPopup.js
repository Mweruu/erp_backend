odoo.define('bi_pos_return_order.ReturnOrderPopup', function(require) {
	'use strict';

	const { useExternalListener } = owl.hooks;
	const PosComponent = require('point_of_sale.PosComponent');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { useState } = owl.hooks;
    var { Gui } = require('point_of_sale.Gui');
	var core = require('web.core');
	var _t = core._t;

	class ReturnOrderPopup extends AbstractAwaitablePopup {
		constructor() {
			super(...arguments);		
		}

		async do_returnOrder(){
			const dateres = await this.check_return_order_date();
			if(!dateres){
				return;
			}
			const res = await this.check_return_qty_passes();
			if(!res){
				return;
			}
			let self = this;
			let selectedOrder = self.env.pos.get_order();
			let orderlines = self.props.orderlines;
			let order = self.props.order;
			let partner_id = false
			let client = false
			if (order && order.partner_id != null){
				partner_id = order.partner_id[0];
				client = self.env.pos.db.get_partner_by_id(partner_id);
			}
			let return_products = {};
			let exact_return_qty = {};
			let exact_entered_qty = {};

			let list_of_qty = $('.entered_item_qty');
			$.each(list_of_qty, function(index, value) {
				let entered_item_qty = $(value).find('input');
				let qty_id = parseFloat(entered_item_qty.attr('qty-id'));
				let line_id = parseFloat(entered_item_qty.attr('line-id'));
				let entered_qty = parseFloat(entered_item_qty.val());
				let returned_qty = parseFloat(entered_item_qty.attr('return-qty'));
				exact_return_qty = qty_id;
				exact_entered_qty = entered_qty || 0;
				let remained = qty_id - returned_qty;

				if(remained < entered_qty){
					alert("Cannot Return More quantity than purchased");
					return;
				}
				else{
					if(!exact_entered_qty){
						return;
					}
					else if (exact_return_qty >= exact_entered_qty){
					  return_products[line_id] = entered_qty;
					}
					else{
						alert("Cannot Return More quantity than purchased");
						return;
					}
				}
			});
			
			$.each( return_products, function( key, value ) {
				orderlines.forEach(function(ol) {
					if(ol.id == key && value > 0){
						let product = self.env.pos.db.get_product_by_id(ol.product_id[0]);
						selectedOrder.add_product(product, {
							quantity: - parseFloat(value),
							price: ol.price_unit,
							discount: ol.discount,
						});
						selectedOrder.set_return_order_ref(ol.order_id[0]);
						selectedOrder.selected_orderline.set_original_line_id(ol.id);
					}
				});
			});

			selectedOrder.set_client(client);
			self.props.resolve({ confirmed: true, payload: null });
			self.trigger('close-popup');
			self.trigger('close-temp-screen');
		}
		get CurrentOrder(){
			return this.env.pos.get_order();
		}
		get CurrentOrderLines(){
			return this.CurrentOrder.orderlines.models.filter((x)=>{ return x.original_line_id != false});
		}
		async check_return_qty_passes(){
			var self = this;
			if(this.CurrentOrder.return_order_ref && this.CurrentOrderLines.length){
				let list_of_qty = $('.entered_item_qty');
				let exact_return_qty = 0;
				let exact_entered_qty = 0;
				var flag = true;
				$.each(list_of_qty, function(index, value) {
					let entered_item_qty = $(value).find('input');
					let qty_id = parseFloat(entered_item_qty.attr('qty-id'));
					let line_id = parseFloat(entered_item_qty.attr('line-id'));
					let entered_qty = parseFloat(entered_item_qty.val());
					let returned_qty = parseFloat(entered_item_qty.attr('return-qty'));
					exact_return_qty = qty_id;
					exact_entered_qty = entered_qty || 0;
					let remained = qty_id - returned_qty;
					var creturn = self.get_retun_current_qty(line_id);
					remained = remained - creturn;
					if(remained < exact_entered_qty){
						alert("Cannot Return More quantity than purchased");
						flag = false;
						return false;
					}
				});
				return flag;
			}
			return true;
		}
		async check_return_order_date(){
			const date1 = new Date(this.props.order.date_order);
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
			return true
		}
		get_retun_current_qty(line_id){
			var lines = this.CurrentOrderLines.filter((x)=>{ return x.original_line_id == line_id});
			var total_retu_qty = 0;
			if(lines.length){
				return lines.map((xx) => { return Math.abs(xx.quantity)}).reduce((rs, sk)=>{ return rs+sk});
			}else{
				return 0;
			}
		}
	}
	
	ReturnOrderPopup.template = 'ReturnOrderPopup';
	Registries.Component.add(ReturnOrderPopup);
	return ReturnOrderPopup;
});
