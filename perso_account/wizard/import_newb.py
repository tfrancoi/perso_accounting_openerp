# -*- coding: utf-8 -*-
'''
    Created on 06 Juillet 2017

    @author: Thibault Francois
'''
import base64
import hashlib
from odoo import models, fields


class ImportNewB(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_newb"
    _description = 'Import File from NewB'

    name = fields.Char(default="Import CSV exported from NewB")
    decimal_separator = fields.Selection(default=',')

    _date_format = "%d/%m/%Y"

    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 14
    _encoding = 'utf-8'

    _cash_flow_mapping = {
        0: "bank_id",
        1: "transaction_date",
        2: "amount",
        4: 'com1',
        8: "com2",
        9: "value_date",
        10: "total",
        13: "reference",
    }

    def _import_rec(self, rec):
        rec['name'] = '{com1}\n{com2}'.format(**rec)
        rec['name'] = rec['name'].strip()
        amount = float(rec['amount'].replace(self._get_thousand_sep(), '').replace(self.decimal_separator, '.'))
        total =  float(rec['total'].replace(self._get_thousand_sep(), '').replace(self.decimal_separator, '.'))
        ref_str = '%s%s%s%s' % (amount, total, rec['transaction_date'], len(rec['name']))
        ref_hash = hashlib.sha1(ref_str.encode('utf-8')).hexdigest()[:4]
        rec['reference'] = '%s-%s' % (rec['reference'], ref_hash)
        del rec['com1']; del rec['com2']; del rec['total']
        return super(ImportNewB, self)._import_rec(rec)
