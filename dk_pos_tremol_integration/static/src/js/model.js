/** @odoo-module **/

import models from 'point_of_sale.models';
import {Order} from 'point_of_sale.models';
import  Registries from "point_of_sale.Registries";
const PosComponent = require('point_of_sale.PosComponent');

const CuIntegration = (Order) => class CuIntegration extends Order {
    constructor() {
        super(...arguments);
        this.l10n_ke_cu_serial_number = this.l10n_ke_cu_serial_number || false;
        this.l10n_ke_cu_datetime = this.l10n_ke_cu_datetime || false;
        this.l10n_ke_cu_invoice_number = this.l10n_ke_cu_invoice_number|| false;
        this.l10n_ke_cu_qrcode = this.l10n_ke_cu_qrcode || false;
        this.reversed_entry_id = this.reversed_entry_id || false;
        this.manual_etr = this.manual_etr || false;
    }
//send order data to send to the server
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments)
        json.l10n_ke_cu_serial_number = this.l10n_ke_cu_serial_number;
        json.l10n_ke_cu_datetime = this.l10n_ke_cu_datetime;
        json.l10n_ke_cu_invoice_number = this.l10n_ke_cu_invoice_number;
        json.l10n_ke_cu_qrcode = this.l10n_ke_cu_qrcode;
        json.reversed_entry_id = this.reversed_entry_id;
        json.manual_etr = this.manual_etr;
        return json;
    }

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.l10n_ke_cu_serial_number = json.l10n_ke_cu_serial_number;
        this.l10n_ke_cu_datetime = json.l10n_ke_cu_datetime;
        this.l10n_ke_cu_invoice_number =json.l10n_ke_cu_invoice_number;
        this.l10n_ke_cu_qrcode = json.l10n_ke_cu_qrcode;
        this.reversed_entry_id = json.reversed_entry_id;
        this.manual_etr = json.manual_etr;

    }
    export_for_printing() {
        var json = super.export_for_printing(...arguments);
        json.l10n_ke_cu_serial_number = this.l10n_ke_cu_serial_number;
        json.l10n_ke_cu_datetime = this.l10n_ke_cu_datetime;
        json.l10n_ke_cu_invoice_number = this.l10n_ke_cu_invoice_number;
        json.l10n_ke_cu_qrcode = this.l10n_ke_cu_qrcode;
        json.manual_etr = this.manual_etr;
        return json;
    }

};
Registries.Model.extend(Order, CuIntegration);
