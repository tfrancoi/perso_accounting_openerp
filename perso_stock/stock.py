# -*- coding: utf-8 -*-
from openerp.osv.orm import Model  
from openerp.osv import fields,osv

from openerp import models, fields


class stock_move(models.Model):
    _name = 'perso.stock.move'
    _order = "create_date desc"
    
    product_id      = fields.Many2one("perso.product", string="Product", index=True)
    type            = fields.Selection([('in', 'Incoming'), ('out', 'Outgoing')], string="Type of move") 
    quantity        = fields.Float("Quantity")
    reference       = fields.Char("Reference")
    unit_of_measure = fields.Char(string="Unit of Measure", related="product_id.unit_of_measure", readonly=True)
    
    
    
class stock_service(Model):
    _name = 'perso.stock.service'
    
    def find_product(self, cr, uid, reference):
        ref_obj = self.pool['perso.product.reference']
        ref_ids = ref_obj.search(cr, uid, [('name', '=', reference)]) 
        if not ref_ids:
            return False
        res = []
        for ref in ref_obj.browse(cr, uid, ref_ids):
            res.append([ref.product_id.id, ref.product_id.name, ref.product_id.unit_of_measure] + [ref.name for ref in ref.product_id.reference_ids])
        return res
    
    def get_product_by_name(self, cr, uid, name):
        product_obj = self.pool['perso.product']
        product_ids = product_obj.search(cr, uid, [('name', 'ilike', name)])
        res = []
        for product in product_obj.browse(cr, uid, product_ids):
            res.append([product.id, product.name, product.unit_of_measure] + [ref.name for ref in product.reference_ids])
        return res
    
    def create_product(self, cr, uid, reference, name, unit_of_measure):
        product_obj = self.pool['perso.product']
        value =  {
            "name" : name,
            "unit_of_measure" : unit_of_measure,
        }
        if reference:
            value["reference_ids"] = [(0, 0, {'name' : reference})]
        print value
        return product_obj.create(cr, uid, value)
    
    def get_product_without_ref(self, cr, uid):
        product_obj = self.pool['perso.product']
        product_ids = product_obj.search(cr, uid, [('reference_ids', '=', False)])
        res = []
        for product in product_obj.browse(cr, uid, product_ids):
            res.append([product.id, product.name, product.unit_of_measure])
        return res
    
    def _move(self, cr, uid, product_id, qty, reference, move_type):
        print "move_type", move_type
        if move_type not in ('in', 'out'):
            return False
        
        value = {
            "product_id" : product_id,
            "type" : move_type,
            "quantity" : qty,
            "reference" : reference,
        }
        return self.pool['perso.stock.move'].create(cr, uid, value)
    
    def move_in(self, cr, uid, product_id, qty, reference):
        return self._move(cr, uid, product_id, qty, reference, 'in')
        
    def move_out(self, cr, uid, product_id, qty, reference):
        return self._move(cr, uid, product_id, qty, reference, 'out')
        
            
        