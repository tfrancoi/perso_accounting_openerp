# -*- coding: utf-8 -*-
'''
    Created on 6 May 2014

    @author: Thibault Francois
'''
from openerp import models, fields, api

class LoadChartOfAccount(models.TransientModel):

    _name = "perso.account.load_chart_of_account"

    period_id = fields.Many2one("perso.account.period", string="Period")
    bank_id   = fields.Many2one("perso.bank.account", string="Bank Account")

    @api.multi
    def open(self):
        context = { 'hide_empty_account' : True }
        if self.bank_id:
            context['bank_id'] = self.bank_id.name
        if self.period_id:
            context['period_id'] = self.period_id.name

        context['hide_empty_account'] = True

        view_id = self.env.ref('perso_account.view_account_tree_tree').id

        return {
            'name': 'Chart of account',
            'view_type': 'tree',
            'view_mode': 'tree',
            'view_id' : view_id,
            'res_model': 'perso.account',
            'type': 'ir.actions.act_window',
            'context': context
        }
