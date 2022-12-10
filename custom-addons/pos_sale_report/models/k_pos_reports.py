from datetime import datetime,time
from odoo import models, fields

class POSDifferenceReport(models.Model):
    _name="pos.order.report.diffs"

    user_id =  fields.Many2one('res.users' )
    date_from = fields.Date(default=datetime.now())
    date_to = fields.Date(default=datetime.now())

    def action_print_difference_report(self):
        data = []

        domain = []
        domain_user = []
        if self.date_from:
            domain +=[('create_date','>=',self.date_from)]
        if self.date_to:
            # convert to datatime
            dt= datetime.combine(self.date_to, time( hour=23, minute=59, second=59 ))
            domain +=[('create_date','<=',dt)]          
        if self.user_id:
            domain_user+= [('user_id' ,'=', self.user_id.id)]

        pos =  self.env['pos.order'].search_read(domain) 
        
        domain += [('price_unit',">=", 0)]
        orders = self.env['pos.order.line'].search_read(domain,order='id')
        for order in orders:
            # create a datamodel
            product = self.env['product.product'].search_read([('id', '=',order['product_id'][0])])[0]        
            if not order['price_unit'] == product['lst_price']:
                date =  order['create_date']      
                domain_user += [('id','=',[0])]

                user=''
                pos_no =''
            
                for po in pos:
                    if (po['id'] == order['order_id'][0]):
                        user = po['user_id'][1]
                        pos_no = po['pos_reference']
                
                if user =='' or pos_no =='':
                    continue

                product_id =  product['partner_ref']
                qty =  order['qty']
                sale =  order['price_unit']
                fixed =  product['lst_price']
                diff =  round(sale -  fixed, 2)
                tot = round(diff * qty, 2)
 

                data.append({
                        'date':date,
                        'user':user,  
                        'pos_no':pos_no,
                        'product_id':product_id,
                        'qty' :qty,
                        'sale' :sale,
                        'fixed' :fixed,
                        'diff':diff,
                        'tot' :tot 
                    }
                )
        # sort
        k=0; 
        while k < len(data)-1:
            i =0
            while i < len(data)-1:
                if data[i]['tot'] > data[i+1]['tot']:
                    swap = data[i] 
                    data[i] = data[i+1] 
                    data[i+1] = swap               
                i+=1
            k+=1
  
        data={
            'records': data,
            'self': self.read()[0]
        }
        return self.env.ref('pos_sale_report.k_pos_orders_transactions_report').report_action(self, data = data)