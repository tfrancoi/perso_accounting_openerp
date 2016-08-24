# -*- coding: utf-8 -*-
'''
    Created on 6 May 2014

    @author: Thibault Francois
'''
from openerp import api, fields, models, _
from openerp.exceptions import UserError

class distribution(models.TransientModel):

    _name = "perso.account.distribution"

    name                  = fields.Char("Name", default="Distribution")
    cash_flow_id          = fields.Many2one("perso.account.cash_flow", string="Cash flow to ventilate", required=True)
    amount                = fields.Float(compute="_get_amount", string="Cash Flow Amount")
    account_regulation_id = fields.Many2one('perso.account', string="Compensation Cash Flow Account", required=True)
    line_ids              = fields.One2many("perso.account.distribution.line", "wizard_id", string="Ventilation Lines")
    template_id           = fields.Many2one('perso.account.distribution_template', string="Template")

    @api.one
    @api.depends('cash_flow_id')
    def _get_amount(self):
        self.amount = self.cash_flow_id and self.cash_flow_id.amount or 0.0

    @api.onchange('cash_flow_id')
    def onchange_cash_flow(self):
        if self.cash_flow_id:
            self.account_regulation_id = self.cash_flow_id.account_id.id
        else:
            self.account_regulation_id = False

    @api.one
    def confirm(self):
        reference = self.cash_flow_id.reference
        cash_flow_to_create = [{
            'reference' : "%s-0" % reference,
            'name' : "Regulation for " + self.cash_flow_id.name,
            'account_id': self.account_regulation_id.id,
            'bank_id' : self.cash_flow_id.bank_id.id,
            'value_date' : self.cash_flow_id.value_date,
            'transaction_date' : self.cash_flow_id.transaction_date,
            'amount' : -self.amount,
            'distributed' : True,
            
        }]

        amount_sum = 0.0
        for i, line in enumerate(self.line_ids):
            amount_sum += line.amount
            cash_flow_to_create.append({
                'reference' : "%s-%s" % (reference,  i+1),
                'name' : line.name,
                'account_id': line.account_id.id,
                'bank_id' : self.cash_flow_id.bank_id.id,
                'value_date' : line.value_date,
                'transaction_date' : self.cash_flow_id.transaction_date,
                'amount' : line.amount,
            
            })
            
        if self.amount - amount_sum > 0.001 or self.amount - amount_sum < -0.001:
            raise UserError(_('Amount does not match'))
        
        for cash_flow in cash_flow_to_create:
            self.env['perso.account.cash_flow'].create(cash_flow)
            
        self.cash_flow_id.distributed = True

    def _reload(self):
        return {
            'type' : "ir.actions.act_window",
            'res_model' : 'perso.account.distribution',
            'view_mode' : 'form',
            'target' : "new",
            'res_id' : self.id
        }

    @api.multi
    def save_as_template(self):
        self.ensure_one()
        self.name
        lines = []
        for line in self.line_ids:
            lines.append((0,0,{
                "name" : line.name,
                "amount" : line.amount,
                "account_id" : line.account_id.id,
            }))

        values = {
            'name' : self.name,
            'line_ids' : lines,
        }
        self.env['perso.account.distribution_template'].create(values)
        
        return self._reload()

    @api.multi
    def load_template(self):
        self.ensure_one()
        if not self.template_id:
            raise UserError(_('Please select a template before loading it'))

        line_to_create = []

        for line in self.template_id.line_ids:
            line_to_create.append([0,0, {
                'name' : line.name,
                'amount' : line.amount,
                'account_id' : line.account_id.id,
                'value_date' : self.cash_flow_id.value_date,
            }])
        self.write({'line_ids' : [(6,0,[])] + line_to_create})

        return self._reload()


class ventilation_line(models.TransientModel):
    _name = "perso.account.distribution.line" 

    name       = fields.Char("Description", required=True)
    amount     = fields.Float("Amount", required=True)
    account_id = fields.Many2one('perso.account', string="Account", required=True)
    value_date = fields.Date("Value Date", required=True)
    wizard_id  = fields.Many2one('perso.account.distribution', string="Wizard")
