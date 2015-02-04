# -*- coding: utf-8 -*-

from openerp import models, fields, api

class product_reference(models.Model):
    _name = "perso.product.reference"
    
    name = fields.Char("Reference", required=True)
    product_id = fields.Many2one("perso.product", string="Product", required=True, ondelete="cascade")
    
class product(models.Model):
    
    _name = "perso.product"

    name = fields.Char("Name", required=True)
    reference_ids = fields.One2many("perso.product.reference", "product_id", string="Reference")
    unit_of_measure = fields.Char("Unit of Measure", default="Unit")
    move_ids = fields.One2many("perso.stock.move", "product_id")
    quantity = fields.Float(compute="_get_quantity", string="Quantity", readonly=True, store=True)
    
    @api.one
    @api.depends('move_ids', 'move_ids.quantity')
    def _get_quantity(self):
        quantity = 0
        for move in self.move_ids:
            if move.type == 'in':
                quantity += move.quantity
            elif move.type == 'out': 
                quantity -= move.quantity
        self.quantity = quantity
   
    