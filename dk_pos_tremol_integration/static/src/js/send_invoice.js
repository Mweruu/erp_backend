odoo.define('dk_pos_tremol_integration.postSend', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const core = require('web.core');
    const ajax = require('web.ajax');
    const Dialog = require('web.Dialog');
    var rpc = require('web.rpc');
    var _t = core._t;


    const postSend = (PaymentScreen) => class extends PaymentScreen {
        async post_send_pos(response){
            try {
                let res = await this.env.services.rpc({
                    model: 'tremol.queue',
                    method: 'queue_tremol',
                    args: [response.params.invoices.proxy_address + '/hw_proxy/l10n_ke_cu_send',
                    response.params.invoices.messages,response.params.invoices.company_vat]
                });
                const res_obj =  JSON.parse(res)
                if (res_obj && res_obj.status === "ok") {
                    let replies = res_obj.replies.map(msg => msg);
                    this.currentOrder.l10n_ke_cu_serial_number = res_obj.serial_number;
                    this.currentOrder.l10n_ke_cu_invoice_number = replies[replies.length - 2].split(';')[0];
                    this.currentOrder.l10n_ke_cu_qrcode = replies[replies.length - 2].split(';')[1].trim();
                    this.currentOrder.l10n_ke_cu_datetime = replies[replies.length - 1];
                    this.currentOrder.manual_etr = false
                } else {
//                    this.currentOrder.l10n_ke_cu_serial_number = 'KRAMW011202207061142';
//                    this.currentOrder.l10n_ke_cu_invoice_number = '0110611420000018390';
//                    this.currentOrder.l10n_ke_cu_qrcode = 'https://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0110611420000018390';
//                    this.currentOrder.manual_etr = false;
                    this.currentOrder.manual_etr = true;
                    console.log("status: ", JSON.stringify(res_obj), res_obj.status)
                    throw new Error(_t("Posting an invoice has failed, with the message: \n") + res_obj.message + "::::" + res_obj.status + "\n\n\n Issue a manual ETR!! ")
                }
            } catch(error) {
                console.log("Error:post_send_pos" , JSON.stringify(error))
                this.currentOrder.manual_etr = true;
                const middleWareMessage = ' Error trying to connect to the middleware. Is the middleware running? Unable to fetch data from Tims. Issue a manual ETR';
                throw new Error(_t( error.message? error.message : middleWareMessage));
            }
        }
    }
    Registries.Component.extend(PaymentScreen, postSend);
    return postSend;

});
