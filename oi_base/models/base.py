'''
Created on Sep 18, 2018

@author: Zuhair Hammadi
'''
from odoo.models import BaseModel
from odoo import models, api, fields,_
import datetime
import re
import uuid
import string
import random
from odoo.tools.misc import format_datetime
from collections import defaultdict
from operator import itemgetter

def normilize(*names, record_id = False):
    name = ' '.join(filter(None,names))
    text= re.sub(r'\W',' ', name.lower()).strip().replace(' ', '_')
    res =[]
    non_ascii = False
    for char in text:
        if ord(char) > 128:
            non_ascii = True
            continue
        res.append(char)
    if non_ascii and record_id:
        res.append(str(record_id))
    return ''.join(res)
         

def remove_duplicates(lines):
    res = []
    added = set()
    for vals in lines:
        value = (vals['field'],vals['old_value'],vals['new_value'],vals['user'],vals['date'])
        if value in added:
            continue
        added.add(value)
        res.append(vals)
    return res

class Base(models.AbstractModel):
    _inherit ='base'
    
    @api.model
    def _base(self, model = 'base'):
        return type(self.env[model])
        
    def _read_field(self, field):
        """
        :param field name
        :return: dictionary mapping record id with field value
        """
        res = self.read([field])
        res = {record['id'] : record[field] for record in res}
        return res
    
    def _suggest_external_id(self):
        if self._name =='ir.model.fields':
            return normilize(self._name, self.model, self.name) 
        return normilize(self._name, 'code' in self and isinstance(self['code'], str) and len(self['code']) < 20 and self['code'] or '', self.display_name, record_id = self.id)
    
    def _create_external_id(self):
        ref = self.get_external_id().get(self.id)        
        if not ref:
            IrModelData = self.env['ir.model.data']
            if self._context.get('is_approval_setting'):
                vals = {'module' : '_workflow',
                        'name' : self._suggest_external_id(),
                        'noupdate' : True
                    }
            else:
                vals = {'module' : '_',
                        'name' : self._suggest_external_id()
                    }
            while IrModelData.search(self._dict_to_domain(vals)):
                vals['name'] = '%s_%s' % (vals['name'], uuid.uuid4().hex[:6])            
            vals.update({
                'model' : self._name,
                'res_id' : self.id
                })
            ref=IrModelData.create(vals).complete_name     
        return ref       
        
    @api.model
    def _isinstance(self, model):
        return isinstance(self, type(self.env[model]))
    
    @api.model
    def _get_sql_value(self, sql, para = ()):
        self._cr.execute(sql, para)
        res=self._cr.fetchone()
        res= res and res[0] or False
        if isinstance(res, datetime.datetime):
            return fields.Datetime.to_string(res)
        if isinstance(res, datetime.date):
            return fields.Date.to_string(res)
        return res     
    
    @api.model
    def _dict_to_domain(self, vals):
        domain = []
        for key, value in vals.items():
            if isinstance(value, (dict,list,tuple )):
                value = str(value)
            domain.append((key, '=', value))
        return domain
    
    def get_title(self):        
        return '%s | %s' % (self.env['ir.model']._get(self._name).name, self.display_name)    
    
    def get_form_url(self):
        return '/web#id=%d&model=%s&view_type=form' % (self.id, self._name)
        
    def _expand_group_all(self, records, domain, order):
        return records.search([], order = order)

    def onchange(self, values, field_name, field_onchange):
        self = self.with_context(onchange_field_name = field_name, onchange_model = self._name)
        return super(Base, self).onchange(values, field_name, field_onchange)        
    
    def _onchange_eval(self, field_name, onchange, result):
        self = self.with_context(onchange_eval_field_name = field_name)
        return super(Base, self)._onchange_eval(field_name, onchange, result)       
    
    def _hierarchical_sort(self, parent_name = None):
        parent_name = parent_name or self._parent_name or 'parent_id'
        vals = {}
        for record in self:
            parent = record
            level = 0
            recursion_test = set()
            while parent[parent_name]:
                level +=1
                parent = parent[parent_name]
                if parent in recursion_test:
                    break
                recursion_test.add(parent)
            vals[record] = level
            
        return self.sorted(key = lambda record : (vals[record], record.display_name))
    
    def _selection_name(self, field_name):
        if not self:
            return False
        names = dict(self._fields[field_name]._description_selection(self.env))
        value = self[field_name]
        return names.get(value, value)   
    
    def check_access_rule(self, operation):
        if not any(self.ids):
            return
        return super(Base, self).check_access_rule(operation)
 
    def _child_of(self, others, parent=None):
        "return True if self child of others"
        if not (isinstance(others, BaseModel) and others._name == self._name):
            raise TypeError("Comparing apples and oranges: %s._child_of(%s)" % (self, others))
        parent_name = parent or self._parent_name
        current = self
        while current:
            if current in others:
                return True
            current = current[parent_name]
               
    def _action_view_one2many(self, field_name):
        field = self._fields[field_name]
        assert field.type == 'one2many'
        return {
            'type' : 'ir.actions.act_window',
            'name' : self.env['ir.model.fields']._get(self._name, field.name).field_description,
            'res_model' : field.comodel_name, 
            'view_mode' : 'tree,form',
            'domain' : [(field.inverse_name,'=', self.id)],
            'context' : {
                'default_' + field.inverse_name : self.id
                }
            }    
    
    def open_window_action_records(self, records, name = None, ctx = {}):
        action = {
            'type' : 'ir.actions.act_window',
            'res_model' : '%s' % records._name,
            'context': ctx,
            }
        if len(records) == 1:
            action.update({
                'view_mode' : 'form',
                'res_id' : records.id                        
                })        
        else:
            action.update({
                'view_mode' : 'tree,form',
                'domain' : [('id','in', records.ids)],
                'name' : name or records._description,                  
                })        
        
        return action   
        
    def _random_password(self, length = 16, chars = None):
        chars = list(chars or (string.ascii_letters + string.digits + string.punctuation))
        random.shuffle(chars)
        res = []
        for _ in range(length):
            res.append(random.choice(chars))
        
        return ''.join(res)
    
    def get_group_emails(self, groups):
        if isinstance(groups, str):
            groups = groups.split(',')
        res = self.env['res.groups'].with_context(active_test = True)
        for xmlid in groups:
            res += self.env.ref(xmlid)
        return ';'.join(filter(None,res.mapped('users.employee_ids.work_email')))       
    
    
    def _groupby(self, key):
        groups = defaultdict(self.browse)
        
        if isinstance(key, str):
            key = itemgetter(key)
                        
        for record in self:
            groups[key(record)] |= record
            
        return groups.items() 
        
    def get_record_info(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        
        model_id = self.env['ir.model']._get_id(self._name)
                        
        data = {
            'id' : self.id,
            'model' : self._name,
            'name' : self.display_name,
            'create_date' : 'create_date' in self and format_datetime(self.env, self.create_date),
            'create_uid' : 'create_uid' in self and self.create_uid.sudo().display_name,
            'write_date' : 'write_date' in self and format_datetime(self.env, self.write_date),
            'write_uid' : 'write_uid' in self and self.write_uid.sudo().display_name,
            'lines' : [],
            'tracking_value_count' : 0,
            'log_count' : 0,
            'update_log_count' : 0
            }
        
        
        model_data = self.env['ir.model.data'].sudo().search([('model','=', self._name), ('res_id','=', self.id)], order = 'id', limit = 1)
        if model_data:
            data['xmlid'] = model_data.complete_name
            data['noupdate'] = model_data.noupdate
            data['xmlid_id'] = model_data.id
        else:
            data['suggest_xmlid'] = self._suggest_external_id()
                
        if 'audit.log' in self.env:
            log_ids = self.env['audit.log'].sudo().search([('record_id','=', self.id), ('model_id','=', model_id), ('type','=', '3')]).ids
            data['log_count'] = self.env['audit.log'].sudo().search([('record_id','=', self.id), ('model_id','=', model_id)], count = True)
            
            message_ids = self.env['mail.message'].search([('model','=', self._name), ('res_id','=', self.id)])
            data['tracking_value_count'] = self.env['mail.tracking.value'].search([('mail_message_id','in', message_ids.ids)], count = True)
            
        else:
            log_ids = []
            message_ids = []
        
                
        if log_ids:
            data['update_log_count'] = self.env['audit.log.detail'].sudo().search([('log_id','in', log_ids)], count = True)
            for detail in  self.env['audit.log.detail'].sudo().search([('log_id','in', log_ids)], order = 'id desc', limit = 100):                
                data['lines'].append({
                    'field' : detail.field_id.field_description,
                    'old_value' : detail.old_value_display,
                    'new_value' : detail.new_value_display,
                    'user' : detail.log_id.user_id.display_name,
                    'date' : format_datetime(self.env, detail.log_id.date),
                    'id' : detail.id,
                    'date_value' : detail.log_id.date
                    })
            
        if message_ids:
            tracking_value_ids = self.env['mail.tracking.value'].search([('mail_message_id','in', message_ids.ids)], order='id desc', limit = 100)                        
            for value_id in tracking_value_ids:
                data['lines'].append({
                    'field' : value_id.field_desc,
                    'old_value' : value_id._get_old_display_value()[0],
                    'new_value' : value_id._get_new_display_value()[0],
                    'user' : value_id.create_uid.display_name,
                    'date' : format_datetime(self.env, value_id.create_date),
                    'id' : value_id.id,
                    'date_value' : value_id.create_date
                    })             
                                     
        data['lines'] = sorted(data['lines'], key = lambda vals: (vals['date_value'], vals['id']), reverse = True )
        
        data['lines'] = remove_duplicates(data['lines'])
        
        data['lines'] = data['lines'][:100]
        
        for vals in data['lines']:
            vals.pop('id')
            vals.pop('date_value')
                    
        return data        
    
        
    def view_fields_with_data(self):
        fields = self.check_field_access_rights('read', None)
        model_id = self.env['ir.model']._get_id(self._name)
        return {
            'type' : 'ir.actions.act_window',
            'res_model' : 'ir.model.fields',
            'name' : _('View Data'),
            'views' : [(self.env.ref("oi_base.view_ir_model_fields_tree_data").id, 'list')],
            'domain' : [('model_id','=', model_id), ('name','in', fields)],
            'context' : {
                'record_id' : self.id
                }
            }