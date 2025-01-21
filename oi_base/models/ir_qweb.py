'''
Created on Apr 19, 2023

@author: Zuhair Hammadi
'''
from odoo import models
from .arabic_number import amount_to_text_ar, en_to_ar

class IrQweb(models.AbstractModel):
    _inherit = "ir.qweb"
    
    def _prepare_environment(self, values):
        values.update({
            'en_to_ar' : en_to_ar,
            'amount_to_text_ar' : amount_to_text_ar            
            })
        return super()._prepare_environment(values)
    