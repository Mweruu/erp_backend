{
    "name":"POS Daily Sales Reports",
    "version":"1.0",
    "category":"Productivity",
    "depends":['point_of_sale'],
    "description":"""
    
    This Dashboard provides an overview of total sales in the POS module,
    Sales per individual salespersons, their daily totals, and the total refunds per salesperson.

    The dashboard also allows the Accountant to get an overview of total sales of the day and Attempt to balance with the Cash-In-Hand amount.
    
     """,
    "data":[ 
        "security/ir.model.access.csv",      
        "views/k_pos_daily_reports.xml"
    ],
    'license': 'LGPL-3',
}