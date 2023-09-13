// bi_pos_return_order js
odoo.define('bi_pos_return_order.models', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var field_utils = require('web.field_utils');
	var { Gui } = require('point_of_sale.Gui');
	var core = require('web.core');
	var _t = core._t;

	var posorder_super = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			this.return_order_ref = this.return_order_ref || false;
			posorder_super.initialize.call(this,attr,options);
		},

		set_return_order_ref: function (return_order_ref) {
			this.return_order_ref = return_order_ref;
		},

		export_as_JSON: function() {
			var json = posorder_super.export_as_JSON.apply(this,arguments);
			json.return_order_ref = this.return_order_ref  || false;
			return json;
		},

		init_from_JSON: function(json){
			posorder_super.init_from_JSON.apply(this,arguments);
			this.return_order_ref = json.return_order_ref || false;
		},

	});


	var OrderlineSuper = models.Orderline.prototype;
	models.Orderline = models.Orderline.extend({

		initialize: function(attr, options) {
			OrderlineSuper.initialize.call(this,attr,options);
			this.original_line_id = this.original_line_id || false;
		},
		can_be_merged_with: function(orderline){
			var res = OrderlineSuper.can_be_merged_with.apply(this,arguments);
			if(res){
				if(this.original_line_id){
					return false;
				}
			}
			return res;
		},
		set_original_line_id: function(original_line_id){
			this.original_line_id = original_line_id;
			this.trigger('change');
		},

		get_original_line_id: function(){
			return this.original_line_id;
		},
		clone: function(){
        	var orderline = OrderlineSuper.clone.call(this);
	        orderline.original_line_id = this.original_line_id;
	        return orderline;
	    },
		export_as_JSON: function() {
			var json = OrderlineSuper.export_as_JSON.apply(this,arguments);
			json.original_line_id = this.original_line_id || false;
			return json;
		},
		
		init_from_JSON: function(json){
			OrderlineSuper.init_from_JSON.apply(this,arguments);
			this.original_line_id = json.original_line_id;
		},
		returnCurrentOrderLines: function(retun_line_id){
			return this.order.orderlines.models.filter((x)=>{ return x.original_line_id == retun_line_id});
		},
		set_quantity: async function(quantity, keep_price){
			var flag = true;
			if(quantity != 'remove'){
				var quant = typeof(quantity) === 'number' ? quantity : (field_utils.parse.float('' + quantity) || 0);
				if (this.original_line_id) {
					if(quant > 0){
						Gui.showPopup('ErrorPopup', {
	                        title: _t('Positive quantity not allowed'),
	                        body: _t('Only a negative quantity is allowed for this return order line. Click on +/- to modify the quantity to be Return.')
	                    });
	                    flag = false;
	                    return false;
					}
					var crtotal = this.returnCurrentOrderLines(this.original_line_id).map((xx) => { return Math.abs(xx.quantity)}).reduce((rs, sk)=>{ return rs+sk})
					crtotal = crtotal + Math.abs(quant);
					const rline = await this.pos.rpc({
						model: 'pos.order.line',
						method: 'search_read',
						args: [[['id','=',this.original_line_id]]],
					});
					if(rline.length){
						var rqty = rline[0].qty - rline[0].return_qty;
						if(rqty < crtotal){
							Gui.showPopup('ErrorPopup', {
		                        title: _t('Greater than allowed'),
		                        body: _.str.sprintf(
		                            _t('The requested quantity to be return is higher than the returnable quantity of %s.'),
		                            this.pos.formatProductQty(rqty)
		                        ),
		                    });
		                    flag = false;
		                    return false;
						}
					}
				}
			}
			return OrderlineSuper.set_quantity.apply(this,arguments);
		}

	});

});