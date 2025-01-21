'''
Created on Oct 4, 2021

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'
    
    default_ids = fields.One2many('ir.default', 'field_id', string = 'User-defined Defaults')
    record_value = fields.Char(compute = '_calc_record_value')
    record_display = fields.Char(compute = '_calc_record_value')
            
    @api.depends_context('record_id', 'lang')
    def _calc_record_value(self):
        record_id = self._context.get("record_id")
        for field in self:
            model = self.env[field.model]
            record = model.browse(record_id)
            value = record[field.name]
            display = ','.join(value.sudo().mapped('display_name')) if value and isinstance(value, models.BaseModel) else False
                
            field.record_value = value
            field.record_display = display
    
    def action_open_field(self):        
        return  {
            'type' : 'ir.actions.act_window',
            'res_model' : self._name,
            'name' : self.field_description,
            'views' : [(False, 'form')],
            'res_id' : self.id
            }
    
    def action_open_record(self):
        record_id = self._context.get("record_id")
        model = self.env[self.model]
        record = model.browse(record_id)
        value = record[self.name]
        if not isinstance(value, models.BaseModel):
            return
                
        action = {
            'type' : 'ir.actions.act_window',
            'res_model' : value._name,
            'name' : self.field_description,
            'views' : [(False, 'list'), (False, 'form')],
            'domain' : [('id','in', value.ids)],
            'context' : {
                'form_view_initial_mode' : 'readonly'                
                }
            }
        
        if len(value)<=1:
            action.update({
                'views' : [(False, 'form')],
                'res_id' : value.id
                })
            
        return action