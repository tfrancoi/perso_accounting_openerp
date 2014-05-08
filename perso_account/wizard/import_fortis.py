# -*- coding: utf-8 -*-
'''
    Created on 25 janv. 2014

    @author: Thibault Francois
'''
from openerp.osv.orm import Model, TransientModel
from osv import fields,osv
from datetime import timedelta
from datetime import date
from base64 import b64decode
import csv
from StringIO import StringIO
import datetime


class import_fortis(TransientModel):
    
    _name = "perso.account.import_fortis"
    
    _columns = {
        'name' : fields.char(string="Name"),
        'file' : fields.binary(string="Fortis Export CSV", required=True),
    }  
    
    # Specific to import fortis         
    _defaults = {
        'name' : "Import CSV exported from BNP Paribas Fortis",
    }
    
    _date_format = "%d/%m/%Y"
    
    _decimal_sep = ","
    _csv_delimiter = ";"
    _csv_quote = '"'
    
    _cash_flow_mapping = {
        "ANNEE + REFERENCE": "reference",
        "DATE DE L'EXECUTION": "transaction_date",
        'DATE VALEUR': "value_date",
        'DETAIL': "name",
        'MONTANT': 'amount',
        'NUMERO DE COMPTE': "bank_id",
    }
    #End of specific to import fortis
    
    def _map(self, record):
        mapped_rec = {}
        for k, v in record.items():
            if self._cash_flow_mapping.get(k):
                new_key = self._cash_flow_mapping.get(k)
                mapped_rec[new_key] = v
        return mapped_rec
    
    def _to_iso_date(self, orig_date):
        date_obj = datetime.datetime.strptime(orig_date, self._date_format)  
        return date_obj.strftime('%Y-%m-%d')
    
    def _import_rec(self, cr, uid, rec, context=None):
        bank_ids = self.pool.get('perso.bank.account').search(cr, uid, [('name', '=', rec['bank_id'].strip())])
        if not bank_ids:
            raise Exception("Bank Account %s does not exist" % rec['bank_id'])
        rec['bank_id'] = bank_ids[0]
        rec['amount'] = float(rec['amount'].replace(self._decimal_sep, '.'))
        rec['transaction_date'] = self._to_iso_date(rec['transaction_date'])
        rec['value_date'] = self._to_iso_date(rec['value_date'])
        cash_flow_obj = self.pool.get("perso.account.cash_flow")
        if not cash_flow_obj.search(cr, uid, [('reference', '=', rec['reference'])], context=context):
            cash_flow_obj.create(cr, uid, rec, context=context)
        else:
            print "DO not IMPORT", rec
        
    
    def import_file(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        wizard = self.browse(cr, uid, ids[0], context=context)
        csv_file = StringIO(b64decode(wizard.file))
        data = csv.DictReader(csv_file, delimiter=self._csv_delimiter, quotechar=self._csv_quote)
        for line in data:
            self._import_rec(cr, uid, self._map(line), context)
            
