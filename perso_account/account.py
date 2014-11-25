# -*- coding: utf-8 -*-
from openerp.osv.orm import Model  
from openerp.osv import fields,osv
from datetime import timedelta
from datetime import date

from openerp import models, fields, api

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
    
    name = fields.Char("Name")
    date_start = fields.Date("Date Start")
    date_end = fields.Date("Date End")
    active = fields.Boolean("Active", default=True)
  
    
"""
    Account Model
"""
class account(Model):

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
            cash_flow_domain.append(("period_id", "=", period_ids[0]))
        if bank_ids:
            cash_flow_domain.append(("bank_id", "=", bank_ids[0]))
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
            
        
   
    
    @api.one
    def _get_dummy(self):
        self.period_id = False
        self.bank_id = False

class consolidation_account(Model):
    
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
    

class cash_flow(Model):
    
    _name = "perso.account.cash_flow"

    reference = fields.Char("Reference")
    name = fields.Text("Description")
    account_id = fields.Many2one("perso.account", string="Account")
    bank_id = fields.Many2one("perso.bank.account", string="Bank Account", required=True)  
    value_date = fields.Date("Value Date", required=True)
    transaction_date = fields.Date("Transaction Date")
    amount = fields.Float("Amount", required=True)
    type = fields.Selection(related="account_id.type", string="Type", store=True, readonly=True)
    period_id = fields.Many2one("perso.account.period", compute="_get_period", search="_search_period", string="Period")
    distributed = fields.Boolean("Has been distributed", readonly=True)
    
    _sql_constraints = [
        ('ref_uniq', 'unique (reference)', 'Each reference must be unique.')
    ]
    
    _order = "value_date desc"
    
    @api.multi
    @api.depends('value_date')
    def _get_period(self):
        period_obj = self.env["perso.account.period"]
        for period in period_obj.search([]):
            cash_flow = self.search([("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end), ('id', 'in', self.ids)])
            for cash in cash_flow:
                cash.period_id = period

    def _search_period(self, operator, period_id):
        period = self.env["perso.account.period"].browse(period_id)
        cash_ids = self.search([("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end)])
        return [('id', 'in', cash_ids.ids)]
        #Bug openerp
        #return [("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end)]
    

