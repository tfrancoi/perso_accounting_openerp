# -*- coding: utf-8 -*-
'''
    Created on 06 Juillet 2017

    @author: Thibault Francois
'''
import base64
import hashlib
from odoo import models, fields


class ImportAxa(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_axa"
    _description = 'Import File from Axa'

    name = fields.Char(default="Import CSV exported from Axa")
    decimal_separator = fields.Selection(default='.')

    _date_format = "%d/%m/%Y"

    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 9
    _encoding = 'utf-8'

    _cash_flow_mapping = {
        0: "value_date",
        1: "amount",
        2: "reference",
        4: 'com2',
        5: 'com3',
        6: 'com4',
        7: 'com5',
        8: "bank_id",
    }

    def _import_rec(self, rec):
        rec['transaction_date'] = rec['value_date']
        com = ' : '.join(filter(lambda l: l.strip(), [rec['com3'], rec['com4']]))
        rec['name'] = '\n%s\n%s\n%s' % (rec['com5'], rec['com2'], com)
        rec['name'] = rec['name'].strip()
        rec['reference'] = '%s/%s/%s' % (rec['value_date'], rec['amount'].replace('.', ''), rec['reference'].replace('.', ''))
        del rec['com2']; del rec['com3']; del rec['com4']; del rec['com5']
        return super(ImportAxa, self)._import_rec(rec)
