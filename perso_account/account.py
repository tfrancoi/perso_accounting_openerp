# -*- coding: utf-8 -*-
from openerp.osv.orm import Model  
from osv import fields,osv
from datetime import timedelta
from datetime import date

"""
    Configuration Model
"""
class bank_account(Model):
    
    _name = "perso.bank.account"
    
    _columns = {
        "name" : fields.char("Name", required=True),
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Each name must be unique.')
    ]

class perso_account_period(Model):
    
    _name = 'perso.account.period'
    
    _columns = {
        'name' : fields.char("Name"),
        'date_start' : fields.date("Date Start"),
        'date_end' : fields.date("Date End"),
        'active' : fields.boolean("Active"),
    }
    
    _defaults = {
        'active' : True,
    }
    
  
    
"""
    Account Model
"""
class account(Model):

    _name = "perso.account"
    def _get_all_child(self, account, result):
        if not account.child_ids:
            return list(set(result))
        else:
            for child in account.child_ids:
                result.extend(self._get_all_child(child, list(result)))
                result.append(child.id)
            return list(set(result))
        
    def _get_amount(self, cr, uid, ids, fields, arg, context=None):
        context = context or {}
        period_ids = False
        bank_ids = False
        if context.get("period_id"):
            period_ids = self.pool.get("perso.account.period").search(cr, uid, [('name', '=', context["period_id"])], context=context)
        
        if context.get("bank_id"):
            bank_ids = self.pool.get("perso.bank.account").search(cr, uid, [('name', '=', context["bank_id"])], context=context)
        #Compute ids needed for computation
        compute_ids = list(ids)
        for account in self.browse(cr, uid, ids, context=context):
            compute_ids.extend(self._get_all_child(account, []))
            
        compute_ids = list(set(compute_ids))
            
        parent_per_child = {}
        budget_per_account = {}
        for account in self.browse(cr, uid, compute_ids, context=context):
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
        cash_flow_obj = self.pool.get('perso.account.cash_flow')
        cash_flow_ids = cash_flow_obj.search(cr, uid, cash_flow_domain, context=context)
        for cash_flow in cash_flow_obj.browse(cr, uid, cash_flow_ids, context=context):
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
        res = {}
        for account_id in ids:
            res[account_id] = {
                'amount' : amount[account_id], 
                'consolidated_amount' : consolidated_amount[account_id],
                'consolidated_budget' : consolidated_budget[account_id],
            }
        return res
        

    _columns = {
        "name" : fields.char("Name", required=True),
        "parent_id" : fields.many2one("perso.account", string="Parent Account"),
        "child_ids" : fields.one2many("perso.account", "parent_id", string="Children account", readonly=True),
        "cash_flow_ids" : fields.one2many('perso.account.cash_flow', 'account_id', string="Cash Flow"),
        "type" : fields.selection([("revenue", "Revenue"), ("expense", "Expense"), ("root", "Root")], string="Type", required=True),
        "description" : fields.text("Description"),
        "amount" : fields.function(_get_amount, type="float", string="Amount", readonly=True, multi=True),
        "consolidated_amount" : fields.function(_get_amount, type="float", string="Amount Consolidated", readonly=True, multi=True),
        "id" : fields.integer("id"),
        "period_id" : fields.dummy(type="many2one", relation="perso.account.period", string="Period"),
        "bank_id" : fields.dummy(type="many2one", relation="perso.bank.account", string="Bank Account"),
        "budget" : fields.float("Account budget"),
        "consolidated_budget" : fields.function(_get_amount, type="float", string="Consolidated Budget", readonly=True, multi=True),
    }

class consolidation_account(Model):
    
    _name = "perso.account.consolidation"
    
    def _get_amount(self, cr, uid, ids, fields, args, context=None):
        res = dict.fromkeys(ids, {'amount' : 0.0, 'consolidated_amount' : 0.0})
        for conso_account in self.browse(cr, uid, ids, context=context):
            accounts = conso_account.account_ids
            res[conso_account.id] = {
                'amount' : sum([a.amount for a in accounts]),
                'consolidated_amount' : sum([a.consolidated_amount for a in accounts])
            }
        return res
    
    _columns = {
        'name' : fields.char("Name"),
        'description' : fields.text("Description"),
        'account_ids' : fields.many2many("perso.account", string="Accounts"),
        "amount" : fields.function(_get_amount, type="float", string="Amount", readonly=True, multi=True),
        "consolidated_amount" : fields.function(_get_amount, type="float", string="Amount Consolidated", readonly=True, multi=True),
        "period_id" : fields.dummy(type="many2one", relation="perso.account.period", string="Period"),
        "bank_id" : fields.dummy(type="many2one", relation="perso.bank.account", string="Bank Account"),
    }

class cash_flow(Model):
    
    _name = "perso.account.cash_flow"
    
    def _get_period(self, cr, uid, ids, field, arg, context=None):
        res = dict.fromkeys(ids, [])
        period_obj = self.pool.get("perso.account.period")
        all_period_ids = period_obj.search(cr, uid, [], context=context)
        for period in period_obj.browse(cr, uid, all_period_ids, context=context):
            cash_flow_ids = self.search(cr, uid, [("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end), ('id', 'in', ids)], context=context)
            for cash_id in cash_flow_ids:
                res[cash_id] = period.id

        return res

    def _search_period(self, cr, uid, obj, name, args, context=None):
        period_id = args[0][2]
        period = self.pool.get("perso.account.period").browse(cr, uid, period_id, context=context)
        cash_ids = self.search(cr, uid, [("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end)], context=context)
        return [('id', 'in', cash_ids)]
        #Bug openerp
        #return [("value_date", ">=", period.date_start), ("value_date", "<=", period.date_end)]
    
    _columns = {
        "reference" : fields.char("Reference"),
        "name" : fields.text("Description"),
        "account_id" : fields.many2one("perso.account", string="Account"),
        "bank_id" : fields.many2one("perso.bank.account", string="Bank Account", required=True),    
        "value_date" : fields.date("Value Date", required=True),
        "transaction_date" : fields.date("Transaction Date"),
        "amount" : fields.float("Amount", required=True),
        "type" : fields.related("account_id", 'type', string="Type", type="char", store=True),
        "period_id" : fields.function(_get_period, fnct_search=_search_period, type="many2one", relation="perso.account.period", string="Period"),
        "distributed" : fields.boolean("Has been distributed"),
    }
    
    _sql_constraints = [
        ('ref_uniq', 'unique (reference)', 'Each reference must be unique.')
    ]
    
    _order = "value_date desc"

