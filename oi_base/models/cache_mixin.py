'''
Created on Mar 2, 2023

@author: Zuhair Hammadi
'''
from odoo import models, api, tools
from odoo.tools.misc import frozendict

class CacheMixin(models.AbstractModel):
    _name = 'cache.mixin'
    _description = 'Cache Mixin'
    
    @api.model
    @tools.ormcache('tuple(domain)')
    def _search_cached(self, domain):
        return self.sudo().search(domain)._ids
    
    @api.model
    @tools.ormcache('record_id', 'self.env.lang')
    def _read_cached(self, record_id):
        vals = self.sudo().browse(record_id).read([])[0]
        for name, value in vals.items():
            vals[name] = self._fields[name].convert_to_cache(value, self)
        return frozendict(vals)
    
    def _ensured_cached(self):
        vals = self._read_cached(self.id)
        for name,value in vals.items():
            field = self._fields[name]
            self.env.cache.insert_missing(self, field, [value])
            
    @api.model                                          
    def search_cached(self, domain):
        ids = self._search_cached(domain)
        for record_id in ids:
            record = self.browse(record_id)
            record._ensured_cached()        
        return self.browse(ids)                            
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(CacheMixin, self).create(vals_list)
        self.clear_caches()
        if getattr(self, '_auto_update_registry', False):
            self._update_registry()        
        return res

    def write(self, vals):
        res = super(CacheMixin, self).write(vals)
        self.clear_caches()
        if getattr(self, '_auto_update_registry', False):
            self._update_registry()
        return res

    def unlink(self):
        res = super(CacheMixin, self).unlink()
        self.clear_caches()
        if getattr(self, '_auto_update_registry', False):
            self._update_registry()        
        return res            
        
    def _update_registry(self):
        self.env.flush_all()
        self.clear_caches()   
        self.env.reset()               
        self.pool.registry_invalidated = True
        self.pool.setup_models(self._cr)
        