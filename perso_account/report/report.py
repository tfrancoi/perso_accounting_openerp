# -*- coding: utf-8 -*-
from openerp import models, fields, api

class account_report_line(models.Model):
    _name = "perso.account.report_line"
    amount = fields.Float('Amount')
    amount_consolidated = fields.Float('Amount Consolidated')
    period_id = fields.Many2one("perso.account.period", string="Period")
    bank_id = fields.Many2one("perso.bank.account", string="Bank")
    account_id = fields.Many2one("perso.account", string="Account")
    type = fields.Char()
    cumulative_amount = fields.Float("Cumulative Amount")
    cumulative_amount_consolidated = fields.Float("Cumulative Amount Consolidated")
