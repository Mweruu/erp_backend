
{
    "name": "Sale Approval",
    "version": "16.0.1.0.1",
    "category": "Sales Management",
    "license": "AGPL-3",
    "author": "Akretion, "
    "Camptocamp, "
    "Sodexis, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "depends": ["sale_stock", "sales_team"],
    "data": [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "views/res_config_settings.xml",
        "views/sale_view.xml",
    ],
    "installable": True,
}
