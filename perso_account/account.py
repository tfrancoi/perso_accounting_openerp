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

class perso_account_period(Model):
    
    _name = 'perso.account.period'
    
    _columns = {
        'name' : fields.char("Name"),
        'date_start' : fields.date("Date Start"),
        'date_end' : fields.date("Date End"),
    }
    
class user(Model):
    _inherit = 'res.users'
    
    _columns = {
        'context_period_id' : fields.many2one('perso.account.period', string="Current Period"),
        'context_period_date_start' : fields.related('context_period_id', 'date_start', type='date', string="Period Date Start", store=True, readonly=True),
        'context_period_date_end' : fields.related('context_period_id', 'date_end', type='date', string="Period Date End", store=True, readonly=True),
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
        #Compute ids needed for computation
        compute_ids = list(ids)
        for account in self.browse(cr, uid, ids, context=context):
            compute_ids.extend(self._get_all_child(account, []))
            
        compute_ids = list(set(compute_ids))
            
        parent_per_child = {}
        for account in self.browse(cr, uid, compute_ids, context=context):
            parent_per_child[account.id] = account.parent_id.id
            
        #Init Value
        amount = dict.fromkeys(compute_ids, 0.0)
        consolidated_amount = dict.fromkeys(compute_ids, 0.0)
        cash_flow_domain = [('account_id', 'in', compute_ids)]
        if context.get('period_date_start') and context.get('period_date_end'):
            cash_flow_domain.extend([("value_date", ">=", context['period_date_start']), ("value_date", "<=", context['period_date_end'])])
        #Compute direct expense
        cash_flow_obj = self.pool.get('perso.account.cash_flow')
        cash_flow_ids = cash_flow_obj.search(cr, uid, cash_flow_domain, context=context)
        for cash_flow in cash_flow_obj.browse(cr, uid, cash_flow_ids, context=context):
            amount[cash_flow.account_id.id] += cash_flow.amount
        
        for account_id in compute_ids:
            account_amount = amount[account_id]
            consolidated_amount[account_id] += account_amount
            while parent_per_child.get(account_id, False):
                parent_id = parent_per_child[account_id]
                if parent_id in compute_ids:
                    consolidated_amount[parent_id] += account_amount
                account_id = parent_id
            
        #Rearrange result    
        res = {}
        for account_id in ids:
            res[account_id] = {
                'amount' : amount[account_id], 
                'consolidated_amount' : consolidated_amount[account_id],
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
    }

class cash_flow(Model):
    
    _name = "perso.account.cash_flow"
    
    _columns = {
        "reference" : fields.char("Reference"),
        "name" : fields.text("Description"),
        "account_id" : fields.many2one("perso.account", string="Account"),
        "bank_id" : fields.many2one("perso.bank.account", string="Bank Account", required=True),    
        "value_date" : fields.date("Value Date", required=True),
        "transaction_date" : fields.date("Transaction Date"),
        "amount" : fields.float("Amount", required=True),
        "type" : fields.related("account_id", 'type', string="Type", type="char", store=True),
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if context.get('current_month'):
            today = date.today()
            first_day_of_month = date(today.year ,today.month, 1).strftime("%Y-%m-%d")
            month = (today.month + 1) % 12
            year = today.year + 1 if (today.month + 1) % 12 < today.month else today.year
            first_day_of_next_month = date(year, month, 1).strftime("%Y-%m-%d")
            args.extend([("value_date", ">=", first_day_of_month), ("value_date", "<", first_day_of_next_month)])
            
        return super(cash_flow, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    
