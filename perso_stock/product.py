# -*- coding: utf-8 -*-
from openerp.osv.orm import Model  
from openerp.osv import fields,osv

class product_reference(Model):
    _name = "perso.product.reference"
    
    _columns = {
        "name" : fields.char("Reference", required=True),
        "product_id" : fields.many2one("perso.product", string="Product", required=True, ondelete="cascade"),
    }
    
class product(Model):
    
    _name = "perso.product"
    
    def _get_quantity(self, cr ,uid, ids, fields, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        move_obj = self.pool.get("perso.stock.move")
        move_ids = move_obj.search(cr, uid, [('product_id', 'in', ids)], context=context)
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            if move.type == 'in':
                res[move.product_id.id] += move.quantity
            elif move.type == 'out': 
                res[move.product_id.id] -= move.quantity
        return res
        
    
    _columns = {
        "name" : fields.char("Name", required=True),
        "reference_ids" : fields.one2many("perso.product.reference", "product_id", string="Reference"),
        "unit_of_measure" : fields.char("Unit of Measure"),
        "quantity" : fields.function(_get_quantity, type="float", string="Quantity", readonly=True),
    }
    
    _defaults = {
        "unit_of_measure" : "Unit",
    }
    
   
    