# -*- coding: utf-8 -*-
from openerp.osv.orm import Model  
from openerp.osv import fields,osv

from openerp import models, fields, api


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
    
    @api.model
    def find_product(self, reference):
        refs = self.env['perso.product.reference'].search([('name', '=', reference)]) 
        res = []
        for ref in refs:
            res.append([ref.product_id.id, ref.product_id.name, ref.product_id.unit_of_measure] + [ref.name for ref in ref.product_id.reference_ids])
        return res
    
    @api.model
    def get_product_by_name(self, name):
        products = self.env['perso.product'].search([('name', 'ilike', name)])
        res = []
        for product in products:
            res.append([product.id, product.name, product.unit_of_measure] + [ref.name for ref in product.reference_ids])
        return res
    
    @api.model
    def create_product(self, reference, name, unit_of_measure):
        value =  {
            "name" : name,
            "unit_of_measure" : unit_of_measure,
        }
        if reference:
            value["reference_ids"] = [(0, 0, {'name' : reference})]
        return self.env['perso.product'].create(value).id
    
    @api.model
    def get_product_without_ref(self):
        products = self.env['perso.product'].search([('reference_ids', '=', False)])
        res = []
        for product in products:
            res.append([product.id, product.name, product.unit_of_measure])
        return res
    
    def _move(self, product_id, qty, reference, move_type):
        if move_type not in ('in', 'out'):
            return False
        
        value = {
            "product_id" : product_id,
            "type" : move_type,
            "quantity" : qty,
            "reference" : reference,
        }
        return self.env['perso.stock.move'].create(value).id
    
    @api.model
    def move_in(self, product_id, qty, reference):
        return self._move(product_id, qty, reference, 'in')
    
    @api.model    
    def move_out(self, product_id, qty, reference):
        return self._move(product_id, qty, reference, 'out')
        
            
        