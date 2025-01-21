/** @odoo-module **/

import { registry } from "@web/core/registry";

const debugRegistry = registry.category("debug");

export function viewData({ component, env }) {
    const resId = component.model.root.resId;
    //if (!resId) {
    //    return null; // No record
    //}
    return {
        type: "item",
        description: env._t("View Fields With Data"),
        callback: async () => {
			const action = await env.services.orm.call(component.props.resModel, "view_fields_with_data", [resId]);			
            env.services.action.doAction(action);			
        },
        sequence: 321,
    };
}

debugRegistry.category("form").add("viewData", viewData);