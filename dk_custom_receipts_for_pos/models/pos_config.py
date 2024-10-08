# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Afra K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    receipt_design = fields.Many2one('pos.receipt', string="Receipt Design", help="Choose any receipt design")
    design_receipt = fields.Text(related='receipt_design.design_receipt', string='Receipt XML')
    is_custom_receipt = fields.Boolean(string='Is Custom Receipt')
    toggle_sign = fields.Boolean(string='Toggle Sign')
    view_quotation_order = fields.Boolean(string='View Quotation Order')
    view_enter_code = fields.Boolean(string='Redeem Gift Card')
    set_percentage_range = fields.Float(string='Percentage Range (%)', default=0.0)
    set_percentage_range_bool = fields.Boolean("Percentage Range")
