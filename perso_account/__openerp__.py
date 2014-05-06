# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'version': '0.1',
    "category": 'Contact Management',
    'author': 'OpenERP SA',
    'depends': ['base'],
    'website': 'http://www.openerp.com',
    'data': [
        'account_view.xml',
        'cash_flow_view.xml',
        'consolidation_account_view.xml',
        'period_view.xml',
        
        'wizard/import_fortis.xml',
        'data/bank_account.xml',
        'wizard/load_chart_of_account_view.xml',
    ],
    'installable': True,
    'application': True,
    'active': False,
    #'images': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

