# -*- coding: utf-8 -*-
'''
    Created on 25 janv. 2014

    @author: Thibault Francois
'''
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from base64 import b64decode
from StringIO import StringIO
import csv
import datetime


class ImportFortis(models.TransientModel):
    
    _name = "perso.account.import_fortis"
    
    name = fields.Char(string="Name", default="Import CSV exported from BNP Paribas Fortis")
    file_to_import = fields.Binary(string="Fortis Export CSV", required=True)
    
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
    
    def _import_rec(self, rec):
        bank_ids = self.env['perso.bank.account'].search([('name', '=', rec['bank_id'].strip())])
        if not bank_ids:
            raise ValidationError(_("Bank Account %s does not exist") % rec['bank_id'])
        rec['bank_id'] = bank_ids[0].id
        rec['amount'] = float(rec['amount'].replace(self._decimal_sep, '.'))
        rec['transaction_date'] = self._to_iso_date(rec['transaction_date'])
        rec['value_date'] = self._to_iso_date(rec['value_date'])
        cash_flow_env = self.env["perso.account.cash_flow"]
        if not cash_flow_env.search([('reference', '=', rec['reference']), ('bank_id', '=', rec['bank_id'])]):
            cash_flow_env.create(rec)
        
    @api.multi
    def import_file(self):
        self.ensure_one()
        csv_file = StringIO(b64decode(self.file_to_import))
        data = csv.DictReader(csv_file, delimiter=self._csv_delimiter, quotechar=self._csv_quote)
        for line in data:
            self._import_rec(self._map(line))
            
