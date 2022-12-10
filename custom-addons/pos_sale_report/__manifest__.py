{
    "name":"POS and Sales Reports",
    "version":"1.0",
    "category":"Productivity",
    "depends":['sale_management',  'point_of_sale'],
    "description":"Reports for goods sold at price different from the fixed price, ",
    "data":[ 
        "security/ir.model.access.csv",      
        "views/k_pos_wizard.xml",
        "views/k_pos_refund_wizard.xml",
        "views/k_sale_wizard.xml",
        "reports/k_pos_refund_report.xml",
        "reports/k_pos_diff_report.xml",
        "reports/k_sale_diff_report.xml",   
    ],
    'license': 'LGPL-3',
}