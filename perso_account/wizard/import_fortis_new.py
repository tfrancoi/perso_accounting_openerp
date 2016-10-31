# -*- coding: utf-8 -*-
'''
    Created on 31 Octobre 2016

    @author: Thibault Francois
'''
from openerp import models


class ImportFortis(models.TransientModel):

    _inherit = "perso.account.import_fortis"
    _name = "perso.account.import_fortis_new"

    _cash_flow_mapping = {
        0: "reference",
        1: "transaction_date",
        2: "value_date",
        3: 'amount',
        5: "name",
        6: "bank_id",
    }

