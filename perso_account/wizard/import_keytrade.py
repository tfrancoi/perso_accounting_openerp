# -*- coding: utf-8 -*-
'''
    Created on 06 Juillet 2017

    @author: Thibault Francois
'''
import hashlib
from datetime import date
from odoo import models, fields

MONTHS_FR = {
    "JANV.": 1,
    "FÉVR.": 2,
    "MARS": 3,
    "AVR.": 4,
    "MAI": 5,
    "JUIN": 6,
    "JUIL.": 7,
    "AOÛT": 8,
    "SEPT.": 9,
    "OCT.": 10,
    "NOV.": 11,
    "DÉC.": 12,
}

def date_fr_to_iso(date_str):
    parts = date_str.split()
    day = int(parts[1])
    month = MONTHS_FR[parts[2]]
    year = int(parts[3])
    date_obj = date(year, month, day)
    return date_obj.strftime("%Y-%m-%d")

class ImportKeytrade(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_keytrade"
    _description = 'Import File from Keytrade'

    name = fields.Char(default="Import CSV exported from Keytrade")
    bank_id = fields.Many2one('perso.bank.account')
    decimal_separator = fields.Selection(default='.')


    _date_format = "%Y-%m-%d"

    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 3
    _encoding = 'utf-8'

    _cash_flow_mapping = {
        0: "value_date",
        1: "name",
        2: "amount",
    }

    def _import_rec(self, rec):
        if not rec:
            return
        rec['bank_id'] = self.bank_id.name
        rec['value_date'] = date_fr_to_iso(rec['value_date'])
        rec['transaction_date'] = rec['value_date']
        rec['name'] = rec['name'].strip()
        ref_str = '%s%s%s' % (rec['amount'], rec['transaction_date'], len(rec['name']))
        ref_hash = hashlib.sha1(ref_str.encode('utf-8')).hexdigest()[:4]
        rec['reference'] = '%s-%s' % (rec['value_date'], ref_hash)
        return super(ImportKeytrade, self)._import_rec(rec)