# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2016 Thibault Francois (<thibault@françois.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Personnal Accounting module',
    'description' : "Manage your personnal finance",
    'version': '1.0',
    "category": 'Perso Account',
    'author': 'Thibault Francois',
    'depends': ['base'],
    'website': 'https://github.com/tfrancoi/perso_accounting_openerp',
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/cash_flow_view.xml',
        'views/consolidation_account_view.xml',
        'views/period_view.xml',
        'views/bank_account.xml',
        'report/report.xml',
        'wizard/distribution.xml',
        'wizard/import_fortis.xml',
        'wizard/import_axa.xml',
        'wizard/import_keytrade.xml',
        'wizard/period_report.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'active': False,
}

#TODO
#Per user, Account and bank account and cash flow and period per user
# Access right
#Perf analysis on report generation