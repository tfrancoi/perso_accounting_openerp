# -*- coding: utf-8 -*-
##############################################################################
#
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
    'name': 'Personnal Asset module',
    'description' : "Manage your personnal asset, store ticket and invoice for warranty, know when warranty ends",
    'version': '1.0',
    "category": 'Account',
    'author': 'Perso Account',
    'depends': ['perso_account'],
    'website': 'https://github.com/tfrancoi/perso_accounting_openerp',
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/asset_view.xml',
    ],
    'installable': True,
    'application': False,
    'active': False,
}
