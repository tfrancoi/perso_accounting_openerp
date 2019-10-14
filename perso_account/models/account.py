# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

"""
    Configuration Model
"""
class BankAccount(models.Model):

    _name = "perso.bank.account"
    _description = "Bank Account"
    _order = "sequence asc"

    name        = fields.Char("Number", required=True)
    description = fields.Char("Description")
    sequence    = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Each name must be unique.')
    ]

    @api.multi
    @api.depends('name', 'description')
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s' % (rec.description, rec.name)))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            name_list = name.split('-')
            name = name_list[-1].strip()
            description = '-'.join(name_list[:-1]).strip()
            if not description:
                domain = ['|', ('name', operator, name), ('description', operator, name)]
            else:
                domain = [('name', operator, name), ('description', operator, description)]
        banks = self.search(domain + args, limit=limit)
        return banks.name_get()

class AccountPeriodType(models.Model):

    _name = 'perso.account.period_type'
    _description = 'Type of Period'

    name = fields.Char()

class AccountPeriod(models.Model):

    _name = 'perso.account.period'
    _description = 'Period'
    
    _order = 'date_start asc'

    name               = fields.Char("Name")
    date_start         = fields.Date("Date Start")
    date_end           = fields.Date("Date End")
    active             = fields.Boolean("Active", default=True)
    previous_period_id = fields.Many2one('perso.account.period')
    line_ids           = fields.One2many('perso.account.report_line', 'period_id')
    type_id            = fields.Many2one('perso.account.period_type')


    def _get_previous_line(self):
        lines = {}
        for line in self.previous_period_id.line_ids:
            lines[(line.bank_id.id, line.account_id.id)] = line
            
        return lines

    def _close_period(self):
        self.ensure_one()
        previous_lines = self._get_previous_line()

        repot_env = self.env['perso.account.report_line']
        repot_env.search([("period_id", '=', self.id)]).unlink()
        for bank in self.env['perso.bank.account'].search([]):
            accounts = self.env['perso.account'].with_context(period_id=self.name, bank_id=bank.name).search([])
            for account in accounts:
                previous_line = previous_lines.get((bank.id, account.id), repot_env)
                if not account.amount and not account.consolidated_amount \
                   and not previous_line.cumulative_amount and not previous_line.cumulative_amount_consolidated:
                    continue
                repot_env.create({
                    'period_id' : self.id,
                    'bank_id': bank.id,
                    'account_id' : account.id,
                    'type' : account.type,
                    'amount' : account.amount,
                    'amount_consolidated' : account.consolidated_amount,
                    'period_type_id' : self.type_id.id,
                    'cumulative_amount': previous_line.cumulative_amount + account.amount,
                    'cumulative_amount_consolidated' : previous_line.cumulative_amount_consolidated + account.consolidated_amount
                })

"""
    Account Model
"""
class Account(models.Model):

    _name = "perso.account"
    _description = 'Classification Account'
    _order = "number asc"

    name                = fields.Char("Name", required=True)
    number              = fields.Char("Number", help="Allow to define your order")
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
    budget              = fields.Float(compute="_get_amount", inverse="_set_budget", string="Account budget")
    consolidated_budget = fields.Float(compute="_get_amount", string="Consolidated Budget", readonly=True)
    last_period_budget  = fields.Float(compute="_get_amount", string="Last Period Budget")
    remaining_budget    = fields.Float(compute="_get_amount", string="Remaining Consolidated Budget", readonly=True)
    is_budget           = fields.Boolean("Is Budget Account", default=False)
    budget_line_ids     = fields.One2many('perso.account.budget.line', 'account_id', string="Budget Lines")

    previous_amount                    = fields.Float(compute="_get_amount", string="Last Period Amount")
    previous_consolidated_amount       = fields.Float(compute="_get_amount", string="Last Period Amount Consolidated")
    past_year_mean_amount              = fields.Float(compute="_get_amount", string="Past Year Mean Amount")
    past_year_mean_consolidated_amount = fields.Float(compute="_get_amount", string="Past Year Mean Consolidated Amount")
    last_period_budget_consolidated    = fields.Float(compute="_get_amount", string="Last Period Consolidated Budget")

    @api.multi
    def _get_all_child(self, account, result):
        if not account.child_ids:
            return list(set(result))
        else:
            for child in account.child_ids:
                result.extend(self._get_all_child(child, list(result)))
                result.append(child.id)
            return list(set(result))

    def _get_cash_domain(self, account_ids, period_ids, bank_ids):
        cash_flow_domain = [('account_id', 'in', account_ids)]
        if period_ids:
            cash_flow_domain.append(("period_id", "in", period_ids.ids))
        if bank_ids:
            cash_flow_domain.append(("bank_id", "in", bank_ids.ids))
        return cash_flow_domain

    def _get_period(self):
        """
            Return the search period
            Return the previous period
            Return the last 12 periods
        """
        if not self._context.get("period_id"):
            return False, False, False

        period = self.env["perso.account.period"]
        if self._context["period_id"] == "current":
            today = fields.Date.today()
            period_ids = period.search([('date_start', '<=', today), ('date_end', '>=', today)], limit=1, order="date_start desc")
        else:
            period_ids = period.search([('name', '=', self._context["period_id"])])

        if not len(period_ids) == 1:
            return period_ids, False, False

        past_year = period.search([('type_id', '=', period_ids.type_id.id), ('date_end', '<', period_ids.date_start)], limit=12, order="date_start desc")
        return period_ids, period_ids.previous_period_id, past_year

    def _get_bank(self):
        bank_ids = False
        if self._context.get("bank_id"):
            bank_ids = self.env["perso.bank.account"].name_search(self._context["bank_id"])
            bank_ids = self.env["perso.bank.account"].browse([b[0] for b in bank_ids])
        if self._context.get("bank_ids"):
            bank_ids = self.env["perso.bank.account"].browse(self._context.get("bank_ids"))

        return bank_ids

    @api.multi
    def _get_amount(self):
        cash_flow_obj = self.env['perso.account.cash_flow']
        bank_ids = self._get_bank()
        period_ids, previous_period_id, past_year_ids = self._get_period()

        #Compute ids needed for computation
        compute_ids = list(self.ids)
        for account in self:
            compute_ids.extend(self._get_all_child(account, []))
        compute_ids = list(set(compute_ids))
            
        parent_per_child = {}
        for account in self.browse(compute_ids):
            parent_per_child[account.id] = account.parent_id.id

        domain = [('account_id', 'in', compute_ids)] + ([('period_id', 'in', period_ids.ids)] if period_ids else [])
        budget_lines = self.env['perso.account.budget.line'].read_group(domain, ['amount'], ['account_id'])
        #import pdb; pdb.set_trace()
        #Compute direct expense
        budget_per_account = dict.fromkeys(compute_ids, 0.0)
        for line in budget_lines:
            budget_per_account[line['account_id'][0]] = line['amount']

        amount = dict.fromkeys(compute_ids, 0.0)
        consolidated_amount = dict.fromkeys(compute_ids, 0.0)
        cash_flow_domain = self._get_cash_domain(compute_ids, period_ids, bank_ids)
        for cash_flow in cash_flow_obj.search(cash_flow_domain):
            amount[cash_flow.account_id.id] += cash_flow.amount

        last_month_amount = dict.fromkeys(compute_ids, 0.0)
        last_month_consolidated_amount = dict.fromkeys(compute_ids, 0.0)
        previous_month_budget = dict.fromkeys(compute_ids, 0.0)
        if previous_period_id:
            previous_cash_flow_domain = self._get_cash_domain(compute_ids, previous_period_id, bank_ids)
            for cash_flow in cash_flow_obj.search(previous_cash_flow_domain):
                last_month_amount[cash_flow.account_id.id] += cash_flow.amount

            domain = [('account_id', 'in', compute_ids), ('period_id', '=', previous_period_id.id)]
            budget_lines_prev = self.env['perso.account.budget.line'].read_group(domain, ['amount'], ['account_id'])
            for line in budget_lines_prev:
                previous_month_budget[line['account_id'][0]] = line['amount']



        past_year_amount = dict.fromkeys(compute_ids, 0.0)
        past_year_consolidated_amount = dict.fromkeys(compute_ids, 0.0)
        if past_year_ids:
            past_year_cash_flow_domain = self._get_cash_domain(compute_ids, past_year_ids, bank_ids)
            for cash_flow in cash_flow_obj.search(past_year_cash_flow_domain):
                past_year_amount[cash_flow.account_id.id] += cash_flow.amount
        
        consolidated_budget = dict.fromkeys(compute_ids, 0.0)
        remaining_consolidated_budget = dict.fromkeys(compute_ids, 0.0)
        last_period_consolidated_budget = dict.fromkeys(compute_ids, 0.0)


        for account_id in compute_ids:
            account_amount = amount[account_id]
            budget = budget_per_account[account_id]
            amount_last_month = last_month_amount[account_id]
            amount_past_year = past_year_amount[account_id]
            previous_budget = previous_month_budget[account_id]

            consolidated_amount[account_id] += account_amount
            consolidated_budget[account_id] += budget
            last_period_consolidated_budget[account_id] += previous_budget
            last_month_consolidated_amount[account_id] += amount_last_month
            past_year_consolidated_amount[account_id] += amount_past_year
            remaining_consolidated_budget[account_id] += account_amount - budget
            while parent_per_child.get(account_id, False):
                parent_id = parent_per_child[account_id]
                if parent_id in compute_ids:
                    consolidated_budget[parent_id] += budget
                    last_period_consolidated_budget[parent_id] += previous_budget
                    consolidated_amount[parent_id] += account_amount
                    last_month_consolidated_amount[parent_id] += amount_last_month
                    past_year_consolidated_amount[parent_id] += amount_past_year
                    remaining_consolidated_budget[parent_id] +=  account_amount - budget
                account_id = parent_id
            

        #Rearrange result    
        for account in self:
            account.budget = budget_per_account[account.id]
            account.consolidated_budget = consolidated_budget[account.id]
            account.last_period_budget = previous_month_budget[account.id]
            account.last_period_budget_consolidated = last_period_consolidated_budget[account.id]
            account.amount = amount[account.id]
            account.consolidated_amount = consolidated_amount[account.id]
            account.previous_amount = last_month_amount[account.id]
            account.previous_consolidated_amount = last_month_consolidated_amount[account.id]
            account.past_year_mean_amount = past_year_amount[account.id] / len(past_year_ids or [1])
            account.past_year_mean_consolidated_amount = past_year_consolidated_amount[account.id] / len(past_year_ids or [1])
            account.remaining_budget = remaining_consolidated_budget[account.id]

    def _set_budget(self):
        budget_line = self.env['perso.account.budget.line']
        if not 'period_id' in self.env.context:
            self = self.with_context(period_id='current')
        period_ids, _, _ = self._get_period()
        print(period_ids)
        if len(period_ids) > 1:
            raise UserError('Cannot write on budget if more then one period given in the context')
        if not period_ids:
            raise UserError('No Current Period found')

        for rec in self:
            line = budget_line.search([('period_id', '=', period_ids.id), ('account_id', '=', rec.id)])
            if not line:
                budget_line.create({
                    'period_id': period_ids.id,
                    'account_id': rec.id,
                    'amount': rec.budget,
                })
            else:
                line.amount = rec.budget

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


    @api.model
    def get_structure(self):
        def get_child_info(rec):
            return {
                'id': rec.id,
                'number': rec.number,
                'name': rec.name,
                'remaining_budget': round(rec.remaining_budget, 2),
                'amount': round(rec.amount, 2),
                'consolidated_amount': round(rec.consolidated_amount, 2),
                'budget': rec.budget,
                'consolidated_budget': round(rec.consolidated_budget, 2),
                'children': [get_child_info(c) for c in rec.child_ids],
            }

        roots = self.with_context(period_id='current').search([('parent_id', '=', False)])
        roots_data = []
        for root in roots:
            roots_data.append(get_child_info(root))
        return roots_data

class ConsolidationAccount(models.Model):
    
    _name = "perso.account.consolidation"
    _description = 'Consolidation Account'
    
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
    

class CashFlow(models.Model):
    
    _name = "perso.account.cash_flow"
    _description = 'Cash Flow'

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
        if isinstance(period_id, str):
            period = self.env["perso.account.period"].search([('name', operator, period_id)])
        elif isinstance(period_id, list):
            period = self.env["perso.account.period"].browse(period_id)
        else:
            period = self.env["perso.account.period"].browse([period_id])

        domain = []
        for p in period:
            domain.extend(['&', ("value_date", ">=", p.date_start), ("value_date", "<=", p.date_end)])
        domain = ['|'] * int((len(domain) / 3 - 1 )) + domain

        return [('id', 'in', self.search(domain).ids)]

    @api.multi
    def edit(self):
        self.ensure_one()
        return {
            'name': 'Edit Cash Flow',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'perso.account.cash_flow',
            'type': 'ir.actions.act_window',
            'res_id' : self.id,
        }


class BudgetLine(models.Model):
    _name = 'perso.account.budget.line'

    _description = 'Budget Line'

    """
        Migration
        INSERT INTO perso_account_budget_line(amount, account_id, period_id) 
        SELECT perso_account.budget, perso_account.id, period.id FROM perso_account 
        LEFT JOIN (select id from perso_account_period order by date_start desc limit 1) period 
        ON true WHERE budget <> 0;
    """

    account_id = fields.Many2one('perso.account', required=True)
    amount = fields.Float(required=True)
    period_id = fields.Many2one('perso.account.period', required=True)

    _sql_constraints = [
        ('account_period_unique', 'unique (account_id, period_id)', 'Only one budget line allow per account per period')
    ]

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            res[rec.id] = "%s - %s: %s" % (rec.account_id.name, rec.period_id.name, rec.amount)
        return res

