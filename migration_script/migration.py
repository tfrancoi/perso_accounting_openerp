# -*- coding: utf-8 -*-
'''
Created on 26 déc. 2016

@author: Thibault François
'''

from odoo_csv_tools.migrate import Migrator

CONNECTION_FILE_OUT = 'connection_out.conf'
CONNECTION_FILE_IN = 'connection_in.conf'

def mirate_perso_account():
    asset = True
    mortgage = True
    context_out = {'active_test': False}
    migrator = Migrator(CONNECTION_FILE_OUT, CONNECTION_FILE_IN)
    migrator.export_batch_size = 400
    migrator.migrate('perso.account.period_type', [], ['id', 'name'], context_out=context_out)

    migrator.migrate('perso.account.period', ['|', ('active', '=', True), ('active', '=', False)], ['id', 'name', 'type_id/id', 'date_start', 'date_end', 'active'], context_out=context_out)
    migrator.migrate('perso.account.period', ['|', ('active', '=', True), ('active', '=', False), ('previous_period_id', '!=', False)], ['id', 'previous_period_id/id'], context_out=context_out)

    migrator.migrate('perso.bank.account', [], ['id', 'name', 'description', 'sequence'], context_out=context_out)

    migrator.migrate('perso.account', [], ['id', 'number', 'name', 'type', 'description', 'is_budget'], context_out=context_out)
    migrator.migrate('perso.account', [('parent_id', '!=', False)], ['id', 'parent_id/id'], context_out=context_out)
    migrator.migrate('ir.filters', [], ['id', 'name', 'model_id/id', 'is_default', 'active', 'domain', 'context', 'sort'], context_out=context_out)

    # migrator.migrate('perso.account.consolidation', [], ['id', 'name', 'description', 'account_ids/id'])

    migrator.import_batch_size = 100
    migrator.migrate('perso.account.cash_flow', [], ['id', 'reference', 'name', 'account_id/id', 'bank_id/id',
                                                    'value_date', 'transaction_date', 'amount', 'distributed'], context_out=context_out)
    migrator.migrate('perso.account.budget.line', [('account_id', '!=', False)], ['id', 'amount', 'period_id/id', 'account_id/id'], context_out=context_out)

    migrator.migrate('perso.account.distribution_template', [], ['id', 'name'], context_out=context_out)
    migrator.migrate('perso.account.distribution_template.line', [], ['id', 'name', 'amount', 'template_id/id', 'account_id/id'], context_out=context_out)

    if asset == True:
        migrator.migrate('perso.account.asset', [], ['id', 'name', 'cash_flow_id/id', 'start_date', 'end_date', 'value'], context_out=context_out)
        migrator.export_batch_size = 5
        migrator.migrate('perso.account.asset_document', [], ['id', 'name', 'fname', 'data', 'asset_id/id'], context_out=context_out)
        migrator.export_batch_size = 400

    if mortgage == True:
        migrator.migrate("perso.bank.mortgage", [], ['id', 'name', 'rate', 'duration', 'amount', 'monthly_rate', 'monthly_payement',
                                                    'total_cost', 'state', 'target_principal_account/id', 'target_interest_account/id'
                                                    ], context_out=context_out)
        migrator.migrate("perso.bank.mortgage.line", [], ['id', 'mortgage_id/id', 'period_nb',
                                                        'principal_paid', 'interest_paid', 'remaining_principal', 'state', 'cash_flow_id/id',
                                                        'counter_cash_flow_id/id', 'principal_cash_flow_id/id', 'interest_cash_flow_id/id',], context_out=context_out)


def migrate_mtg():
    context_out = {'active_test': False}
    migrator = Migrator(CONNECTION_FILE_OUT, CONNECTION_FILE_IN)
    migrator.export_batch_size = 400
    migrator.import_batch_size = 100
    migrator.migrate('mtg.set', [], ['id', 'name', 'code', 'info'], context_out=context_out)
    migrator.migrate('mtg.type', [], ['id', 'name', 'color'], context_out=context_out)
    migrator.migrate('mtg.color', [], ['id', 'name', 'color'], context_out=context_out)
    migrator.migrate('mtg.card', [], [
        'id', 'name', 'color_ids/id', 'text', 'text_back', 'mana_cost',
        'main_type_id/id', 'type_ids/id',
        'super_type_id/id', 'subtype_ids/id'
    ], context_out=context_out)

    migrator.migrate('mtg.card.variant', [], [
        'id', 'card_id/id', 'set_id/id', 'uuid', 'set_number', 'info', 'info_back',
        'image_url', 'image_url_back', 'multiverse_id', 'multiverse_id_back',
        'rarity', 'quantity', 'quantity_foil', 'show_back', 'image', 'image_back',
    ], context_out=context_out)

migrate_mtg()
# mirate_perso_account()
