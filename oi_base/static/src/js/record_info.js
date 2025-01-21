/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { _lt } from "@web/core/l10n/translation";
import { useAutofocus } from "@web/core/utils/hooks";
import { CopyButton } from "@web/views/fields/copy_clipboard/copy_button";

const { Component } = owl;

export class RecordInfoDialog extends Component {
    setup() {
        useAutofocus();
        this.copyText = this.env._t("Copy");
        this.successText = this.env._t("Copied");        
        this.space=" ";
    }
    
    get reference() {
		return `${this.props.model},${this.props.id}`;
	}
    
    open_xml_record() {
		const action = {
				name: this.env._t('XML ID'),
	            res_model: 'ir.model.data',
	            res_id : this.props.xmlid_id,        		        	            
	            views: [[false, 'form']],
	            type: 'ir.actions.act_window',
	            view_mode: 'form',
	            context : {
	            	'default_name' : this.props.suggest_xmlid,
	            	'default_model' : this.props.model,
	            	'default_module' : '_',
	            	'default_res_id' : this.props.id
	            }
		};
			
		this.env.services.action.doAction(action);
		this.props.close();	
	} 
	
	open_update_log() {
		const action = {
					name: this.env._t('Audit Log Detail'),
		            res_model: 'audit.log.detail',
		            domain : [['reference', '=', this.reference]],
		            views: [[false, 'list']],
		            type: 'ir.actions.act_window',
		            view_mode: 'tree,form',
				};
		this.env.services.action.doAction(action);
		this.props.close();							
	}
	
	open_chatter_log() {
		const action = {
				name: this.env._t('Chatter Logs'),
	            res_model: 'mail.tracking.value',
	            domain : [['reference', '=', this.reference]],
	            views: [[false, 'list']],
	            type: 'ir.actions.act_window',
	            view_mode: 'tree,form',
	            context : {
	            	tree_view_ref : 'oi_user_audit.view_mail_tracking_value_tree'
	            }
			};		
		this.env.services.action.doAction(action);
		this.props.close();										
	}
	
	open_all_log() {
		const action = {
				name: this.env._t('Audit Log'),
	            res_model: 'audit.log',
	            domain : [['model_id.model', '=', this.props.model], ['record_id','=', this.props.id]],
	            views: [[false, 'list'], [false, 'form']],
	            type: 'ir.actions.act_window',
	            view_mode: 'tree,form',
			};	
		this.env.services.action.doAction(action);
		this.props.close();														
	}
}

RecordInfoDialog.template = "oi_base.record_info";
RecordInfoDialog.components = { Dialog,CopyButton };

RecordInfoDialog.defaultProps = {
    title: _lt("Record Info"),
};
