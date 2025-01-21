/** @odoo-module */

import { ListController } from '@web/views/list/list_controller';
import { FormController } from '@web/views/form/form_controller';
import { patch } from "@web/core/utils/patch";
import {RecordInfoDialog} from '@oi_base/js/record_info';

const action_menu = {
	
	getSelectedRecordIds() {
		const selectedIds = [];
		if (this.model.root.__viewType==='form') {
			selectedIds.push(this.model.root.data.id);
		}
		else if (this.model.root.records) {
			_.each(this.model.root.records, record => {
				if (record.selected)
					selectedIds.push(record.resId);
			});
		}
		
		return selectedIds;
	},
	
	getActiveContext() {
		const context = _.extend({}, this.props.context, {
					    	active_model : this.props.resModel,
					    	active_ids : this.getSelectedRecordIds(),
					    	active_domain : this.model.root.isDomainSelected ? this.props.domain : false
					    });
		if (context.active_domain)
			delete context.active_ids;
		else
			delete context.active_domain;					
			
		return context;	    
	},
	
	getActionService() {
		return this.model.actionService || this.model.action;
	},
	
    getActionMenuItems() {
        const res = this._super();
		const self = this;			
		
		if (this.getSelectedRecordIds().length == 1) {
			res.other.push({
			            key: "record_info",
			            description: this.env._t("Record Info"),
			            callback: async () => {
							const activeIds = self.getSelectedRecordIds();
							const dialogProps = await self.model.orm.call(self.model.root.resModel, "get_record_info", activeIds);
					    	await this.model.dialogService.add(RecordInfoDialog, dialogProps);					
						}
					});					
		}
        return res;		
	}
};

patch(FormController.prototype, 'oi_base_form_controller_action_menu', action_menu);
patch(ListController.prototype, 'oi_base_list_controller_action_menu', action_menu);
