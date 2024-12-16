/** @odoo-module **/

import { Order, PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';
import session from 'web.session';
import concurrency from 'web.concurrency';
import { Gui } from 'point_of_sale.Gui';
import { round_decimals,round_precision } from 'web.utils';
import core from 'web.core';
import { Domain, InvalidDomainError } from '@web/core/domain';
var rpc = require('web.rpc');
var _t = core._t;
const ReceiptScreen = require('point_of_sale.ReceiptScreen');
const PosComponent = require('point_of_sale.PosComponent');
const { isConnectionError } = require('point_of_sale.utils');
const Chrome = require('point_of_sale.Chrome');

const PosValidateShipLaterOrder = (Order) =>
class PosValidateShipLaterOrder extends Order{
    setup(){}

    async _validateOrder(pos_reference) {
        var self = this;
        try
        {
            const order = await this.pos.env.services.rpc({
                model: 'pos.order',
                method: 'search',
                args: [[['pos_reference', 'in', ['Order ' + pos_reference]]]],
            })
            if (order.length === 0) {
                Gui.showPopup('ErrorPopup',{
                    'title': _t('Error'),
                    'body':  _t('Please enter a valid Receipt Number.'),
                });
                return;
            }
            const posOrderId = order[0];
            const pickings = await this.pos.env.services.rpc({
                model: 'stock.picking',
                method: 'search',
                args: [[['pos_order_id', '=', posOrderId]]],
            });
            if (pickings.length === 0){
                Gui.showPopup('ErrorPopup',{
                    'title': _t('Error'),
                    'body':  _t('No matching stock picking found..'),
                });
                return;
            }
            for (let i = 0; i < pickings.length; i++) {
                const pickingId = pickings[i]
                const picking = await this.pos.env.services.rpc({
                    model: 'stock.picking',
                    method: 'read',
                    args: [pickingId, ['state']],
                });
                if (picking[0].state === 'assigned'){
                    this.pos.env.services.rpc({
                        model: 'stock.picking',
                        method: 'button_validate_from_pos',
                        args: [pickings[0]],
                    }).then(function (result)
                    {
                        if (result.response == 'success')
                        {
                            var cmp_logo = 'data:image/png;base64,' + result.delayed_picking_order.company_details.logo;
                            const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
                            let qr_code_svg = new XMLSerializer().serializeToString(codeWriter.write(result.delayed_picking_order.l10n_ke_cu_qrcode, 150, 150));
                            const _qr = 'data:image/svg+xml;base64,' + window.btoa(qr_code_svg);
                            result.delayed_picking_order.l10n_ke_cu_qrcode_encoded = _qr
                            Gui.showScreen('RTDelReprintReceiptScreen',{
                                delayed_picking_order: result.delayed_picking_order,
                                logo: cmp_logo,
                                pos_order: result.pos_order
                            });
                            return true
                        }
                        else if(result.response == 'failure')
                        {
                            Gui.showPopup('ErrorPopup',{
                                'title': _t('Error'),
                                'body':  _t('Error validating order..'),
                            });
                        }
                        else{
                            Gui.showPopup('ErrorPopup',{
                                'title': _t('Error'),
                                'body':  _t('Error validating order..'),
                            });
                        }
                    });
                }
                else if (picking[0].state === 'done'){
                    Gui.showPopup('ErrorPopup',{
                        'title': _t('Error'),
                        'body':  _t('The selected order is already delivered.'),
                    });
                }
                else {
                    Gui.showPopup('ErrorPopup',{
                        'title': _t('Error'),
                        'body':  _t('The selected order picking is in invalid state. Please check with manager.'),
                    });
                }
            }
        } catch(error){
            let errorMessage = error.message? error.message : '';
            let errorCode = error.message ? error.message.code : null

            if (errorCode === -32098) {
                errorMessage = errorMessage + '. ' +  'Network Failure, Please check your internet connection'
            } else if (isConnectionError(error)) {
                errorMessage = errorMessage + '. ' +  'Network Failure, Please check your internet connection'
            } else {
                errorMessage = errorMessage + '. ' +  'Error validating order.'
            }

            Gui.showPopup('ErrorPopup',{
                'title': _t('Error'),
                'body':  _t(errorMessage),
            });
            return;
        }
    }

    mounted() {
        this.inputRef.el.focus();
    }

    getPayload() {
        return this.state.inputValue;
    }

    async validateOrderFromPOS(pos_reference) {
        await this._validateOrder(pos_reference);
    }
}
Registries.Model.extend(Order, PosValidateShipLaterOrder);
return PosValidateShipLaterOrder;
