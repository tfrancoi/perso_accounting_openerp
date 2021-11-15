# -*- coding: utf-8 -*-
'''
    Created on 02 Aout 2020

    @author: Thibault Francois
'''
import hashlib
from odoo import models, fields


class ImportBelfius(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_belfius"
    _description = 'Import File from Belfius'

    name = fields.Char(default="Import CSV exported from Belfius")
    decimal_separator = fields.Selection(default=',')

    _date_format = "%d/%m/%Y"

    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 15
    _encoding = 'iso-8859-1'

    _cash_flow_mapping = {
        0: "bank_id",
        1: "transaction_date",
        8: "name",
        9: "value_date",
        10: 'amount',
        3: 'reference',
    }

    def _import_rec(self, rec):
        rec['bank_id'] = rec['bank_id'].replace(' ', '')
        rec['name'] = rec['name'].strip()
        amount = float(rec['amount'].replace(self._thousand_sep, '').replace(self.decimal_separator, '.'))
        ref_str = '%s%s%s' % (amount, rec['transaction_date'], len(rec['name']))
        ref_hash = hashlib.sha1(ref_str.encode('utf-8')).hexdigest()[:4]
        rec['reference'] = '%s-%s' % (self._to_iso_date(rec['value_date']).replace('-', '/'), ref_hash)
        return super(ImportBelfius, self)._import_rec(rec)

    def _read_header(self, data):
        print([next(data) for _ in range(0,12)]) #remove first line
        #second line contains the bank account number
        super(ImportBelfius, self)._read_header(data)
