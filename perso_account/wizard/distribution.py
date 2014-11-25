# -*- coding: utf-8 -*-
'''
    Created on 6 May 2014

    @author: Thibault Francois
'''
from openerp.osv.orm import TransientModel  
from openerp.osv import fields,osv

class distribution(TransientModel):
    
    _name = "perso.account.distribution"
    
    def _get_amount(self, cr, uid, ids, fields, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        for wizard in self.browse(cr, uid, ids, context=context):
            res[wizard.id] = wizard.cash_flow_id and wizard.cash_flow_id.amount or 0.0
        return res
    _columns = {
        "name" : fields.char("Name"),
        "cash_flow_id" : fields.many2one("perso.account.cash_flow", string="Cash flow to ventilate", required=True),
        "amount" : fields.function(_get_amount, type="float", string="Cash Flow Amount"),
        "account_regulation_id" : fields.many2one('perso.account', string="Compensation Cash Flow Account", required=True),
        "line_ids" : fields.one2many("perso.account.distribution.line", "wizard_id", string="Ventilation Lines"),
    } 
    
    _defaults = {
        "name" : "Distribution"
    }
    
    def onchange_cash_flow(self, cr, uid, ids, cash_id, context=None):
        account_id = False
        amount = 0
        if cash_id:
            cash_flow = self.pool.get("perso.account.cash_flow").browse(cr, uid, cash_id, context=context)
            amount = cash_flow.amount
            account_id = cash_flow.account_id and cash_flow.account_id.id
        return {
            'value' : {
                    'amount' : amount, 
                    'account_regulation_id' : account_id
            }
        }
        
    def confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        wizard = self.browse(cr, uid, ids[0], context=context)
        
        reference = wizard.cash_flow_id.reference
        cash_flow_to_create = []
        cash_flow_to_create.append({
            'reference' : reference + "-0",
            'name' : "Regulation for " + wizard.cash_flow_id.name,
            'account_id': wizard.account_regulation_id.id,
            'bank_id' : wizard.cash_flow_id.bank_id.id,  
            'value_date' : wizard.cash_flow_id.value_date,
            'transaction_date' : wizard.cash_flow_id.transaction_date,
            'amount' : -wizard.amount,
            'distributed' : True,
            
        })
        amount_sum = 0.0
        for i, line in enumerate(wizard.line_ids): 
            amount_sum += line.amount
            cash_flow_to_create.append({
                'reference' : "%s-%s" % (reference,  i+1),
                'name' : line.name,
                'account_id': line.account_id.id,
                'bank_id' : wizard.cash_flow_id.bank_id.id,  
                'value_date' : line.value_date,
                'transaction_date' : wizard.cash_flow_id.transaction_date,
                'amount' : line.amount,
            
            })
        if wizard.amount != amount_sum:
            raise osv.except_osv('Warning!', 'Amount does not match')
        for cash_flow in cash_flow_to_create:
            self.pool.get('perso.account.cash_flow').create(cr, uid, cash_flow, context=context)
            
        self.pool.get('perso.account.cash_flow').write(cr, uid,  wizard.cash_flow_id.id, {'distributed' : True}, context=context)    
        
            
        return
        
        
        
    
class ventilation_line(TransientModel):
    
    _name = "perso.account.distribution.line" 
    
    _columns = {
        "name" : fields.char("Description", required=True),
        "amount" : fields.float("Amount", required=True),
        "account_id" : fields.many2one('perso.account', string="Account", required=True),
        "value_date" : fields.date("Value Date", required=True),
        "wizard_id" : fields.many2one('perso.account.distribution', string="Wizard"),
    } 