# -*- coding: utf-8 -*-
'''
    Created on 2 May 2018

    @author: Thibault Francois
'''
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PeriodReport(models.TransientModel):

    _name = "perso.account.period.report"
    _description = 'Report Remaining Amount Wizard'

    name            = fields.Char('Cash Flow Name Template', required=True)
    bank_id         = fields.Many2one('perso.bank.account', required=True)
    period_id       = fields.Many2one('perso.account.period', string="Period to report", required=True)
    next_period_id  = fields.Many2one('perso.account.period', string="Period to create report cash flow", required=True)
    account_id      = fields.Many2one('perso.account', string="Account to record report", required=True)
    reported_amount = fields.Float(compute='_get_amount', string="Reported Amount")

    @api.depends('period_id', 'bank_id')
    def _get_amount(self):
        for rec in self:
            if rec.bank_id and rec.period_id:
                cash_flow_ids = self.env['perso.account.cash_flow'].search([('period_id', '=', rec.period_id.id), ('bank_id', '=', rec.bank_id.id)])
                rec.reported_amount = sum([c.amount for c in cash_flow_ids])
            else:
                rec.reported_amount = 0.0

    @api.onchange('period_id')
    def _onchange_period(self):
        if self.period_id:
            self.next_period_id = self.env['perso.account.period'].search([('previous_period_id', '=', self.period_id.id)], limit=1)

    def confirm(self):
        self.ensure_one()
        name = "%s %s" % (self.name, self.period_id.name)
        report = self.env['perso.account.cash_flow'].create({
            'reference' : name.lower().replace(' ', '-'),
            'name' : name,
            'account_id': self.account_id.id,
            'bank_id' : self.bank_id.id,
            'value_date' : self.next_period_id.date_start,
            'transaction_date' : self.next_period_id.date_start,
            'amount' : self.reported_amount,
        })

        counter_part_name = "%s Counterpart" % (name)
        counter_report = self.env['perso.account.cash_flow'].create({
            'reference' : counter_part_name.lower().replace(' ', '-'),
            'name' : counter_part_name,
            'account_id': self.account_id.id,
            'bank_id' : self.bank_id.id,
            'value_date' : self.period_id.date_end,
            'transaction_date' : self.period_id.date_end,
            'amount' : -self.reported_amount,
        })

        return {
            'type' : "ir.actions.act_window",
            'res_model' : 'perso.account.cash_flow',
            'view_mode' : 'list,pivot,graph',
            'target' : "current",
            'domain' : [('id', 'in', [counter_report.id, report.id])]
        }
