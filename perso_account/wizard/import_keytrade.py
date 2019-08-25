# -*- coding: utf-8 -*-
'''
    Created on 06 Juillet 2017

    @author: Thibault Francois
'''
import base64
import hashlib
from odoo import models, fields


class ImportKeytrade(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_keytrade"
    _description = 'Import File from Keytrade'

    name = fields.Char(default="Import CSV exported from Keytrade")
    bank_id = fields.Many2one('perso.bank.account')
    decimal_separator = fields.Selection(default=',')


    _date_format = "%d.%m.%Y"

    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 7
    _encoding = 'iso-8859-1'

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
        return super(ImportKeytrade, self)._import_rec(rec)