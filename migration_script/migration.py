# -*- coding: utf-8 -*-
'''
Created on 26 déc. 2016

@author: Thibault François
'''

from odoo_csv_tools.migrate import Migrator

CONNECTION_FILE_OUT = 'connection_out.conf'
CONNECTION_FILE_IN = 'connection_in.conf'
asset = True
mortgage = True

migrator = Migrator(CONNECTION_FILE_OUT, CONNECTION_FILE_IN)
migrator.export_batch_size = 400
migrator.migrate('perso.account.period_type', [], ['id', 'name'])

migrator.migrate('perso.account.period', [('active', 'in', [True, False])], ['id', 'name', 'type_id/id', 'date_start', 'date_end', 'active', 'previous_period_id/id'])
migrator.migrate('perso.account.period', [('active', 'in', [True, False]), ('previous_period_id', '!=', False)], ['id', 'previous_period_id/id'])

migrator.migrate('perso.bank.account', [], ['id', 'name', 'description', 'sequence'])

migrator.migrate('perso.account', [], ['id', 'number', 'name', 'type', 'description', 'budget'])
migrator.migrate('perso.account', [('parent_id', '!=', False)], ['id', 'parent_id/id'])

migrator.migrate('perso.account.consolidation', [], ['id', 'name', 'description', 'account_ids/id'])

migrator.migrate('perso.account.cash_flow', [], ['id', 'reference', 'name', 'account_id/id', 'bank_id/id',
                                                 'value_date', 'transaction_date', 'amount', 'distributed'])

if asset == True:
    migrator.migrate('perso.account.asset', [], ['id', 'name', 'cash_flow_id/id', 'start_date', 'end_date', 'value'])
    migrator.export_batch_size = 5
    migrator.migrate('perso.account.asset_document', [], ['id', 'name', 'fname', 'data', 'asset_id/id'])
    migrator.export_batch_size = 400

if mortgage == True:
    migrator.migrate("perso.bank.mortgage", [], ['id', 'name', 'rate', 'duration', 'amount', 'monthly_rate', 'monthly_payement',
                                                 'total_cost', 'state', 'target_principal_account/id', 'target_interest_account/id'
                                                ])
    migrator.migrate("perso.bank.mortgage.line", [], ['id', 'mortgage_id/id', 'period_nb',
                                                      'principal_paid', 'interest_paid', 'remaining_principal', 'state', 'cash_flow_id/id',
                                                      'counter_cash_flow_id/id', 'principal_cash_flow_id/id', 'interest_cash_flow_id/id',])
