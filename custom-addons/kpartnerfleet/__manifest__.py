{
    "name":"K_PartnerFleet",
    "version":"1.0",
    "category":"Productivity",
    "depends":[ 'base','account', 'fleet', 'contacts', 'purchase', 'sale_management', 'stock'],
    "description":"Fleet Module Extension",
    "data":[ 
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/k_fleet.xml",
        "views/k_partner.xml",
        "views/k_purchase.xml",
        "views/k_invoice.xml",
        "views/k_purchase_report_wizard.xml",
        "reports/k_purchase_report.xml",
        "reports/k_invoice_bill_report.xml",
        "reports/k_purchase_transactions_report.xml",
        "data/email_template.xml"   
    ],
    'license': 'LGPL-3',
}