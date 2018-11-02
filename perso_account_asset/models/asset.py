# -*- coding: utf-8 -*-
'''
Created on 15 oct. 2016

@author: mythrys
'''

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetDocument(models.Model):
    _name = "perso.account.asset_document"
    _description = "Perso Assets Document"

    name = fields.Char("Document Reason")
    fname = fields.Char("Filename")
    data = fields.Binary("File")
    asset_id = fields.Many2one("perso.account.asset" ,"Asset")

class Asset(models.Model):
    _name = "perso.account.asset"
    _description = "Perso Assets"

    name = fields.Char(required=True)
    cash_flow_id = fields.Many2one('perso.account.cash_flow', string="Move")
    start_date = fields.Date('Buy date')
    end_date = fields.Date('End of Warranty')
    value = fields.Float()
    document_ids = fields.One2many('perso.account.asset_document', 'asset_id')

