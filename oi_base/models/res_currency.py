# -*- coding: utf-8 -*-
'''
Created on Aug 19, 2020

@author: Zuhair Hammadi
'''
from odoo import models
from .arabic_number import amount_to_text_ar

class Currency(models.Model):
    _inherit = "res.currency"
    
    def amount_to_text_ar(self, amount):
        self.ensure_one()
        if self.name in ['AED', 'JOD', 'BHD', 'SAR','SYP']:
            info = self.name
        else:
            info = {
                'currencyCode' : self.name,
                'isCurrencyNameFeminine' : False,
                'englishCurrencyName' : self.currency_unit_label,
                'englishPluralCurrencyName' : self.currency_unit_label,
                'englishCurrencyPartName' : self.currency_subunit_label,
                'englishPluralCurrencyPartName' : self.currency_subunit_label,
                'arabic1CurrencyName' : "واحد " + self.currency_unit_label,
                'arabic2CurrencyName' : "اثنان " +self.currency_unit_label,
                'arabic310CurrencyName' : self.currency_unit_label,
                'arabic1199CurrencyName' : self.currency_unit_label,
                'arabic1CurrencyPartName' : self.currency_subunit_label,
                'arabic2CurrencyPartName' : "اثنان " + self.currency_subunit_label,
                'arabic310CurrencyPartName' : self.currency_subunit_label,
                'arabic1199CurrencyPartName' : self.currency_subunit_label,
                'partPrecision' : self.decimal_places,
                'isCurrencyPartNameFeminine' : False
                }
        return amount_to_text_ar(amount, info)