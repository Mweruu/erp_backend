/** @odoo-module **/

import { RPCError } from "@web/core/network/rpc_service";
import { patch } from "@web/core/utils/patch";

patch(RPCError.prototype, "oi_base", {
	set data(errorData) {
		if (errorData && errorData.debug) {
			console.debug(errorData.debug);
		}
		this._data = errorData;		
	},
	
	get data() {
		return this._data;
	}
	
});