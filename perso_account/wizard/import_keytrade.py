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


    _date_format = "%d/%m/%Y"

    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 7
    _encoding = 'utf-8'

    _cash_flow_mapping = {
        0: "reference",
        1: "transaction_date",
        2: "value_date",
        5: 'amount',
        4: "name",
    }

    def _import_rec(self, rec):
        if not rec:
            return
        rec['bank_id'] = self.bank_id.name
        rec['name'] = rec['name'].strip()
        rec['reference'] = rec['reference'].strip()
        rec['amount'] = rec['amount'].replace(' ', '').replace('+', '')
        return super(ImportKeytrade, self)._import_rec(rec)