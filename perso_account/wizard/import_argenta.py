# -*- coding: utf-8 -*-
'''
    Created on 14 Novembre 2021

    @author: Thibault Francois
'''
import datetime
import xlrd
from base64 import b64decode
from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT



class ImportArgenta(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_argenta"
    _description = 'Import File from Argenta'

    name = fields.Char(default="Import xlsx exported from Argenta")
    decimal_separator = fields.Selection(default='.')

    _date_format = "%Y-%m-%d"

    _header_length = 11

    _cash_flow_mapping = {
        0: "bank_id",
        2: "value_date",
        3: 'reference',
        5: 'amount',
        7: "transaction_date",
        4: 'com1',
        9: 'com2',
        10: 'com3',
    }

    def _import_rec(self, rec):
        rec['name'] = '{com1}\n{com2}\n{com3}'.format(**rec)
        rec['name'] = rec['name'].strip()
        del rec['com1']; del rec['com2']; del rec['com3']
        return super(ImportArgenta, self)._import_rec(rec)

    def _get_data(self):
        file = b64decode(self.file_to_import)
        book = xlrd.open_workbook(file_contents=file or b'')
        sheet = book.sheets()[0]
        data = []
        for i in range(sheet.nrows):
            values = []
            for cell in sheet.row(i):
                if cell.ctype is xlrd.XL_CELL_DATE:
                    dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                else:
                    values.append(str(cell.value))
            data.append(values)
        return (d for d in data)
