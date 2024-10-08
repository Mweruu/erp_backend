# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{

    # App information
    'name': 'RMA (Return Merchandise Authorization) in Odoo',
    'version': '15.0.1.2',
    'category': 'Sales',
    'license': 'OPL-1',
    'summary': "Manage Return Merchandize Authorization (RMA) in Odoo. Allow users to manage Return Orders, Replacement, Refund & Repair in Odoo.The RMA solution from Emipro helps to efficiently accept return request from the customer, provide them the option to get a refund, repair or replacement, and accordingly manage various operational aspects in Odoo such as creating return receipts, delivery orders, credit notes, adjusting stock levels, etc.Emipro is also having integration for well known ecommerce solutions or applications named as Woocommerce connector , Shopify connector , magento connector and also we have solutions for Marketplace Integration such as Odoo Amazon connector , Odoo eBay connector , Odoo walmart Connector , Odoo Bol.com connector.Aside from ecommerce integration and ecommerce marketplace integration, we also provide solutions for various operations, such as shipping , logistics , shipping labels , and shipping carrier management with our shipping integration , known as the Shipstation connector.For the customers who are into Dropship business, we do provide EDI Integration that can help them manage their Dropshipping business with our Dropshipping integration or Dropshipper integration It is listed as Dropshipping EDI integration and Dropshipper EDI integration.Emipro applications can be searched with different keywords like Amazon integration , Shopify integration , Woocommerce integration, Magento integration , Amazon vendor center module , Amazon seller center module , Inter company transfer , eBay integration , Bol.com integration , inventory management , warehouse transfer module , dropship and dropshipper integration and other Odoo integration application or module",

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    'website': "https://www.emiprotechnologies.com/",

    # Dependencies
    'depends': ['delivery', 'repair'],

    'data': [
        'report/rma_report.xml',
        'data/rma_reason_ept.xml',
        'data/mail_template_data.xml',
        'data/crm_claim_ept_sequence.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'report/rma_report_template.xml',
        'views/view_account_invoice.xml',
        'views/crm_claim_ept_view.xml',
        'views/view_stock_picking.xml',
        'views/rma_reason_ept.xml',
        'views/view_stock_warehouse.xml',
        'views/sale_order_view.xml',
        'views/repair_order_view.xml',
        'views/claim_reject_message.xml',
        'wizard/view_claim_process_wizard.xml',
        'wizard/create_partner_delivery_address_view.xml',
        'wizard/res_config_settings.xml'
    ],

    # Odoo Store Specific
    'images': ['static/description/RMA-v15.png'],

    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,
    'active': False,
    'price': 249.00,
    'live_test_url': 'https://www.emiprotechnologies.com/free-trial?app=rma-ept&version=15',
    'currency': 'EUR',

}
