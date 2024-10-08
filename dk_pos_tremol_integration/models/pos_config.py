from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_send_to_TIMS = fields.Boolean(string='Is Send Order to TIMS')
    is_set_product_name = fields.Boolean(string='Is to Set Product Name')
    is_product_name = fields.Text(string='Product Name')
    l10n_pos_ke_cu_proxy_address = fields.Char(
        default="http://localhost:8069",
        string='Fiscal Device Proxy Address(POS)',
        help='The address of the proxy server for the fiscal device.',
    )
