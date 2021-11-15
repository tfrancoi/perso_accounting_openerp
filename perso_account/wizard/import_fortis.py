# -*- coding: utf-8 -*-
'''
    Created on 25 janv. 2014

    @author: Thibault Francois
'''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from base64 import b64decode
from io import StringIO
import csv
import datetime


class ImportFortis(models.TransientModel):
    
    _name = "perso.account.import_fortis"
    _description = 'Import File from Fortis'
    
    name = fields.Char(string="Name", default="Import CSV exported from BNP Paribas Fortis")
    file_to_import = fields.Binary(string="Fortis Export CSV", required=True)
    decimal_separator = fields.Selection([('.', 'Dot (.)'), (',', 'Comma (,)')], default='.', required=True)
    
    _date_format = "%d/%m/%Y"
    
    _csv_delimiter = ";"
    _csv_quote = '"'
    _header_length = 8
    _encoding = 'iso-8859-1'

    _cash_flow_mapping = {
        0: "reference",
        1: "transaction_date",
        2: "value_date",
        3: 'amount',
        6: "name",
        7: "bank_id",
    }

    def _import_rec(self, rec):
        rec['bank_id'] = rec['bank_id'].replace(' ', '')
        bank_ids = self.env['perso.bank.account'].search([('name', '=', rec['bank_id'])])
        if not bank_ids:
            raise ValidationError(_("Bank Account %s does not exist") % rec['bank_id'])
        rec['bank_id'] = bank_ids[0].id
        rec['amount'] = float(rec['amount'].replace(self._get_thousand_sep(), '').replace(self.decimal_separator, '.'))
        rec['transaction_date'] = self._to_iso_date(rec['transaction_date'])
        rec['value_date'] = self._to_iso_date(rec['value_date'])
        cash_flow_env = self.env["perso.account.cash_flow"]
        if not cash_flow_env.search([('reference', '=', rec['reference']), ('bank_id', '=', rec['bank_id'])]):
            if len(rec['reference']) == 5 and rec['reference'][-1] == '-':
                return
            return cash_flow_env.create(rec)

    def _read_header(self, data):
        header = []
        while len(header) != self._header_length:
            header = next(data)

    def _get_data(self):
        csv_file = StringIO(b64decode(self.file_to_import).decode(self._encoding))
        return csv.reader(csv_file, delimiter=self._csv_delimiter, quotechar=self._csv_quote)

    #End of specific to import fortis
    def _map(self, record):
        mapped_rec = {}
        for index, v in enumerate(record):
            if self._cash_flow_mapping.get(index):
                new_key = self._cash_flow_mapping.get(index)
                mapped_rec[new_key] = v
        return mapped_rec

    def _to_iso_date(self, orig_date):
        if not orig_date:
            return fields.Date.today()
        date_obj = datetime.datetime.strptime(orig_date, self._date_format)
        return date_obj.strftime('%Y-%m-%d')

    def _get_thousand_sep(self):
        return ',' if self.decimal_separator == '.' else '.'

    def import_file(self):
        self.ensure_one()
        data = self._get_data()
        #remove Header
        self._read_header(data)
        cash_flow_ids = self.env['perso.account.cash_flow']
        for line in data:
            res = self._import_rec(self._map(line))
            if res:
                cash_flow_ids |= res

        return {
            'type' : "ir.actions.act_window",
            'res_model' : 'perso.account.cash_flow',
            'view_mode' : 'list,pivot,graph',
            'target' : "current",
            'domain' : [('id', 'in', cash_flow_ids.ids)]
        }
