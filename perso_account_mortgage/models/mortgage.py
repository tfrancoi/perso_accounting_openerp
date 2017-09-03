# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from decimal import Decimal
from odoo.tools import float_compare



class Mortgage(models.Model):

    _name = "perso.bank.mortgage"

    name = fields.Char("Name", required=True)
    rate = fields.Float(required=True, digits=(8, 6))
    duration = fields.Integer(required=True, help="Duration in month (ie: 20 years is 240)")
    amount = fields.Float(required=True)
    monthly_rate = fields.Float(digits=(14, 12))

    monthly_payement = fields.Float()
    interest_paid = fields.Float(compute='_get_paid_amount', readonly=True, store=True)
    principal_paid = fields.Float(compute='_get_paid_amount', readonly=True, store=True)
    total_cost = fields.Float(readonly=True)
    line_ids = fields.One2many('perso.bank.mortgage.line', 'mortgage_id')
    draft_line_ids = fields.One2many('perso.bank.mortgage.line', 'mortgage_id', domain=[("state", '=', 'draft')])
    confirmed_line_ids = fields.One2many('perso.bank.mortgage.line', 'mortgage_id', domain=[("state", '=', 'confirmed')])
    paid_line_ids = fields.One2many('perso.bank.mortgage.line', 'mortgage_id', domain=[("state", '=', 'paid')])

    state = fields.Selection([('draft', 'Draft'), ('valid', 'Validated'), ('done', 'Done')], default="draft")
    target_principal_account = fields.Many2one("perso.account")
    target_interest_account = fields.Many2one("perso.account")
    cash_flow_id = fields.Many2one('perso.account.cash_flow')
    used_cash_flow_ids = fields.Many2many('perso.account.cash_flow', compute="_get_used_cash_flow")

    def _get_used_cash_flow(self):
        for rec in self:
            cash_flows = self.env['perso.account.cash_flow']
            for line in rec.paid_line_ids:
                cash_flows |= line.cash_flow_id
                cash_flows |= line.counter_cash_flow_id
                cash_flows |= line.interest_cash_flow_id
                cash_flows |= line.principal_cash_flow_id
            rec.used_cash_flow_ids = cash_flows

    @api.depends('confirmed_line_ids.state', 'paid_line_ids.state')
    def _get_paid_amount(self):
        for rec in self:
            rec.interest_paid = sum(rec.paid_line_ids.mapped('interest_paid'))
            rec.principal_paid = sum(rec.paid_line_ids.mapped('principal_paid'))

    @api.multi
    def compute(self):
        self.ensure_one()
        self.line_ids.unlink()
        rate = Decimal(self.rate) / 100
        if not self.monthly_rate:
            monthly_rate = (1 + rate)**(Decimal(1)/Decimal(12.0)) - 1
            self.monthly_rate = monthly_rate * 100
        else:
            monthly_rate = Decimal(self.monthly_rate) / 100

        if not self.monthly_payement:
            monthly_payement = self._find_month_payement(monthly_rate, self.duration, self.amount)
            monthly_payement = Decimal(round(monthly_payement, 2))
            self.monthly_payement = monthly_payement
        else:
            monthly_payement = Decimal(self.monthly_payement)
        self.total_cost, lines = self._morgage_plan(monthly_rate, self.duration, self.amount, monthly_payement)
        for l in lines:
            self.env['perso.bank.mortgage.line'].create(l)

    @api.multi
    def clean(self):
        self.ensure_one()
        self.monthly_rate = 0.0
        self.monthly_payement = 0.0
        self.total_cost = 0.0
        self.line_ids.unlink()

    def _find_month_payement(self, rate_month, duration, capital):
        if not rate_month:
            return capital / duration

        capital = Decimal(capital)
        result = (capital * rate_month) / ( 1 - (1 / (1 + rate_month)**(duration)))
        return result

    def _morgage_plan(self, rate_month, duration, capital, price_month):
        self.ensure_one()
        C = Decimal(capital)
        lines = []
        cost = 0.0
        for i in xrange(1, duration + 1):
            interest = C * rate_month
            c_remb = price_month - interest
            C = C - c_remb
            C = C * 100 / 100
            lines.append({
              'period_nb' : i,
              'principal_paid': round(c_remb, 2),
              'interest_paid':  round(interest, 2),
              'remaining_principal': round(C, 2),
              'mortgage_id' : self.id,
            })
            cost+= round(interest, 2)
        return cost, lines

    def confirm(self):
        self.state = 'valid'
        self.draft_line_ids.write({'state': 'confirmed'})

    def payment(self):
        self.ensure_one()
        if not self.cash_flow_id:
            return
        if float_compare(self.cash_flow_id.amount, -self.monthly_payement, 2) != 0:
            raise ValidationError("Amount does not match monthly payment amount")
        if not self.confirmed_line_ids:
            raise ValidationError("No more line to pay")

        line = self.confirmed_line_ids[0]
        line.cash_flow_id = self.cash_flow_id
        line.state = 'paid'
        if self.target_interest_account and self.target_principal_account:
            ref = self.cash_flow_id.reference
            line.principal_cash_flow_id = self.cash_flow_id.copy(default={
                                                'reference' : ref and ref + "-1" or False,
                                                'amount': -line.principal_paid,
                                                'account_id': self.target_principal_account.id})
            line.interest_cash_flow_id = self.cash_flow_id.copy(default={
                                                'reference' : ref and ref + "-2" or False,
                                                'amount': -line.interest_paid,
                                                'account_id': self.target_interest_account.id})
            line.counter_cash_flow_id = self.cash_flow_id.copy(default={
                                                'reference' : ref and ref + "-counterpart" or False,
                                                'amount': -self.cash_flow_id.amount})
            self.cash_flow_id.distributed = True
        self.cash_flow_id = False

class MortgageLine(models.Model):

    _name = "perso.bank.mortgage.line"

    _rec_name = 'mortgage_id'

    _order = 'period_nb asc'

    mortgage_id = fields.Many2one('perso.bank.mortgage', required=True, ondelete='cascade')
    period_nb = fields.Integer(required=True)
    principal_paid = fields.Float(required=True)
    interest_paid = fields.Float(required=True)
    remaining_principal = fields.Float(required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('paid', 'Paid')], default="draft")
    cash_flow_id = fields.Many2one('perso.account.cash_flow')
    counter_cash_flow_id = fields.Many2one('perso.account.cash_flow')
    principal_cash_flow_id = fields.Many2one('perso.account.cash_flow')
    interest_cash_flow_id = fields.Many2one('perso.account.cash_flow')