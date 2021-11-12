# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import topological_sort

import logging

_logger = logging.getLogger(__name__)

class AccountReportLine(models.Model):
    _name = "perso.account.report_line"
    _description = "Perso Account Report Line"
    _order = 'period_id asc' 


    amount = fields.Float('Amount')
    amount_consolidated = fields.Float('Amount Consolidated')
    period_id = fields.Many2one("perso.account.period", string="Period")
    bank_id = fields.Many2one("perso.bank.account", string="Bank")
    account_id = fields.Many2one("perso.account", string="Account")
    type = fields.Char()
    cumulative_amount = fields.Float("Cumulative Amount")
    cumulative_amount_consolidated = fields.Float("Cumulative Amount Consolidated")
    period_type_id = fields.Many2one('perso.account.period_type')

    @api.model
    def _generate_line(self, period_ids=None):
        pass

