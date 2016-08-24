# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

"""
    Configuration Model
"""
class bank_account(models.Model):
    
    _name = "perso.bank.account"
    
    name = fields.Char("Name", required=True)
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Each name must be unique.')
    ]

class perso_account_period(models.Model):

    _name = 'perso.account.period'
    
    _order = 'date_start asc'

    name = fields.Char("Name")
    date_start = fields.Date("Date Start")
    date_end = fields.Date("Date End")
    active = fields.Boolean("Active", default=True)
    previous_period_id = fields.Many2one('perso.account.period')
    state = fields.Selection([('open', 'Open'), ('closed', 'Closed')], default="open")
    line_ids = fields.One2many('perso.account.report_line', 'period_id')

    def _get_previous_line(self):
        lines = {}
        for line in self.previous_period_id.line_ids:
            lines[(line.bank_id.id, line.account_id.id)] = line
            
        return lines

    @api.multi
    def open_period(self):
        repot_env = self.env['perso.account.report_line']
        repot_env.search([("period_id", '=', self.id)]).unlink()
        self.state = "open"


    @api.multi
    def close_period(self):
        if self.previous_period_id and self.previous_period_id.state != 'closed':
            raise ValidationError(_('please close the previous version before closing this one'))
        previous_lines = self._get_previous_line()

        repot_env = self.env['perso.account.report_line']
        repot_env.search([("period_id", '=', self.id)]).unlink()
        for bank in self.env['perso.bank.account'].search([]):
            accounts = self.env['perso.account'].with_context(period_id=self.name, bank_id=bank.name).search([])
            for account in accounts:
                previous_line = previous_lines.get((bank.id, account.id))
                repot_env.create({
                    'period_id' : self.id,
                    'bank_id': bank.id,
                    'account_id' : account.id,
                    'type' : account.type,
                    'amount' : account.amount,
                    'amount_consolidated' : account.consolidated_amount,
                    'cumulative_amount': (previous_line and previous_line.cumulative_amount or 0.0) + account.amount,
                    'cumulative_amount_consolidated' : (previous_line and \
                                                       previous_line.cumulative_amount_consolidated or 0.0) + \
                                                       account.consolidated_amount
                })
        self.state = 'closed'

"""
    Account Model
"""
class Account(models.Model):

    _name = "perso.account"

    name                = fields.Char("Name", required=True)
    parent_id           = fields.Many2one("perso.account", string="Parent Account")
    child_ids           = fields.One2many("perso.account", "parent_id", string="Children account", readonly=True)
    cash_flow_ids       = fields.One2many('perso.account.cash_flow', 'account_id', string="Cash Flow")
    type                = fields.Selection([("revenue", "Revenue"), 
                                            ("expense", "Expense"), 
                                            ('saving', 'Saving'), 
                                            ('regulation', 'Regulation'),
                                            ("root", "Root"), 
                                            ], string="Type", required=True)
    description         = fields.Text("Description")
    amount              = fields.Float(compute="_get_amount", string="Amount", readonly=True)
    consolidated_amount = fields.Float(compute="_get_amount", string="Amount Consolidated", readonly=True)
    period_id           = fields.Many2one("perso.account.period", compute="_get_dummy", string="Period")
    bank_id             = fields.Many2one("perso.bank.account", compute="_get_dummy", string="Bank Account")
    budget              = fields.Float("Account budget")
    consolidated_budget = fields.Float(compute="_get_amount", string="Consolidated Budget", readonly=True)

    @api.multi
    def _get_all_child(self, account, result):
        if not account.child_ids:
            return list(set(result))
        else:
            for child in account.child_ids:
                result.extend(self._get_all_child(child, list(result)))
                result.append(child.id)
            return list(set(result))
        
    @api.multi
    def _get_amount(self):
        context = self.env.context
        period_ids = False
        bank_ids = False
        if context.get("period_id"):
            period_ids = self.env["perso.account.period"].search([('name', '=', context["period_id"])])
        
        if context.get("bank_id"):
            bank_ids = self.env["perso.bank.account"].search([('name', '=', context["bank_id"])])
        #Compute ids needed for computation
        compute_ids = list(self.ids)
        for account in self:
            compute_ids.extend(self._get_all_child(account, []))
            
        compute_ids = list(set(compute_ids))
            
        parent_per_child = {}
        budget_per_account = {}
        for account in self.browse(compute_ids):
            parent_per_child[account.id] = account.parent_id.id
            budget_per_account[account.id] = account.budget
        #Init Value
        amount = dict.fromkeys(compute_ids, 0.0)
        consolidated_amount = dict.fromkeys(compute_ids, 0.0)
        consolidated_budget = dict.fromkeys(compute_ids, 0.0)
        cash_flow_domain = [('account_id', 'in', compute_ids)]
        if period_ids:
            cash_flow_domain.append(("period_id", "=", period_ids[0].id))
        if bank_ids:
            cash_flow_domain.append(("bank_id", "=", bank_ids[0].id))
        #Compute direct expense
        cash_flow_obj = self.env['perso.account.cash_flow']
        for cash_flow in cash_flow_obj.search(cash_flow_domain):
            amount[cash_flow.account_id.id] += cash_flow.amount
        
        for account_id in compute_ids:
            account_amount = amount[account_id]
            budget_amount = budget_per_account[account_id]
            consolidated_amount[account_id] += account_amount
            consolidated_budget[account_id] += budget_amount
            while parent_per_child.get(account_id, False):
                parent_id = parent_per_child[account_id]
                if parent_id in compute_ids:
                    consolidated_amount[parent_id] += account_amount
                    consolidated_budget[parent_id] += budget_amount
                account_id = parent_id
            
        #Rearrange result    
        for account in self:
            account.amount = amount[account.id]
            account.consolidated_amount = consolidated_amount[account.id]
            account.consolidated_budget = consolidated_budget[account.id]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(Account, self).search(args, offset, limit, order, count=count)
        if self.env.context.get('hide_empty_account'):
            res = res.filtered(lambda x : x.amount != 0.0 or x.consolidated_amount != 0.0)
        return res
    
    @api.one
    def _get_dummy(self):
        self.period_id = False
        self.bank_id = False

class consolidation_account(models.Model):
    
    _name = "perso.account.consolidation"
    
    name                = fields.Char("Name")
    description         = fields.Text("Description")
    account_ids         = fields.Many2many("perso.account", string="Accounts")
    amount              = fields.Float(compute="_get_amount", string="Amount", readonly=True)
    consolidated_amount = fields.Float(compute="_get_amount", string="Amount Consolidated", readonly=True)
    period_id           = fields.Many2one("perso.account.period", string="Period", compute="_get_dummy")
    bank_id             = fields.Many2one("perso.bank.account", string="Bank Account", compute="_get_dummy")
    
    @api.one
    def _get_amount(self):
        accounts = self.account_ids
        self.amount =  sum([a.amount for a in accounts])
        self.consolidated_amount = sum([a.consolidated_amount for a in accounts])

    @api.one
    def _get_dummy(self):
        self.period_id = False
        self.bank_id = False
    

class cash_flow(models.Model):
    
    _name = "perso.account.cash_flow"

    reference           = fields.Char("Reference", copy=False)
    name                = fields.Text("Description")
    account_id          = fields.Many2one("perso.account", string="Account")
    bank_id             = fields.Many2one("perso.bank.account", string="Bank Account", required=True)
    value_date          = fields.Date("Value Date", required=True)
    transaction_date    = fields.Date("Transaction Date")
    amount              = fields.Float("Amount", required=True)
    amount_opposite     = fields.Float(compute="_invert", store=True, string="Amount Inverted")
    type                = fields.Selection(related="account_id.type", string="Type", store=True, readonly=True)
    period_id           = fields.Many2one("perso.account.period", compute="_get_period", search="_search_period", string="Period")
    distributed         = fields.Boolean("Has been distributed", readonly=True)
    
    _sql_constraints = [
        ('ref_uniq', 'unique (reference, bank_id)', 'Each reference must be unique per bank account.')
    ]
    
    _order = "value_date desc"
    
    @api.one
    @api.depends('amount')
    def _invert(self):
        self.amount_opposite = - self.amount
    
    @api.multi
    @api.depends('value_date')
    def _get_period(self):
        period_obj = self.env["perso.account.period"]
        for period in period_obj.search([]):
            cash_flow = self.search([("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end), ('id', 'in', self.ids)])
            for cash in cash_flow:
                cash.period_id = period

    def _search_period(self, operator, period_id):
        if isinstance(period_id, basestring):
            period = self.env["perso.account.period"].search([('name', operator, period_id)])
        else:
            period = self.env["perso.account.period"].browse([period_id])

        domain = [['&', ("value_date", ">=", p.date_start), ("value_date", "<=", p.date_end)] for p in period]
        domain = ['|'] * (len(domain) / 3 - 1 ) + domain

        return [('id', 'in', self.search(domain).ids)]
