'''
Created on Mar 25, 2019

@author: Zuhair Hammadi
'''

from odoo import fields
from unidecode import unidecode

original_to_datetime = fields.Datetime.to_datetime
original_to_date = fields.Date.to_date

def convert(value):
    res = []
    for v in value:
        if v.isdigit():
            v = unidecode(v)
        res.append(v)
    return ''.join(res)

@staticmethod
def to_datetime(value):    
    if isinstance(value, str):
        value = convert(value)        
    return original_to_datetime(value)

fields.Datetime.to_datetime = to_datetime
fields.Datetime.from_string = to_datetime

@staticmethod
def to_date(value):    
    if isinstance(value, str):
        value = convert(value)        
    return original_to_date(value)

fields.Date.to_date = to_date
fields.Date.from_string = to_date