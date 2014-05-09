# -*- coding: utf-8 -*-
'''
    Created on 6 May 2014

    @author: Thibault Francois
'''
from openerp.osv.orm import TransientModel  
from osv import fields,osv


class load_chart_of_account(TransientModel):
    
    _name = "perso.account.load_chart_of_account"
    
    _columns = {
        "period_id" : fields.many2one("perso.account.period", string="Period"),
        "bank_id" : fields.many2one("perso.bank.account", string="Bank Account"),
    } 
    
    def open(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        if wizard.bank_id:
            context['bank_id'] = wizard.bank_id.name
        if wizard.period_id:
            context['period_id'] = wizard.period_id.name
            
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'perso_account', 'view_account_tree_tree')[1]
            
        return {
            'name': 'Chart of account',
            'view_type': 'tree',
            'view_mode': 'tree',
            'view_id' : view_id,
            'res_model': 'perso.account',
            'type': 'ir.actions.act_window',
            'context': context
                
        }
