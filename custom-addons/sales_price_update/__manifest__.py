{
    "name":"Sales Price Update",
    "version":"1.0",
    "category":"",
    "depends":['base','sale_management',  'point_of_sale','purchase'],
    "description":"This report shows the old price and current price of a product ",
    "data":[
        "security/ir.model.access.csv",
        "views/sales_price_difference.xml",
        "reports/sales_price_update-report.xml",

    ],
    'license': 'LGPL-3',
}