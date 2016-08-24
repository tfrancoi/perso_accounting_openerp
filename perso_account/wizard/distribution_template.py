# -*- coding: utf-8 -*-
'''
    Created on 14 June 2015

    @author: Thibault Francois
'''
from openerp import fields, models

class distribution_template(models.Model):

    _name = "perso.account.distribution_template"

    name     = fields.Char("Name")
    line_ids = fields.One2many("perso.account.distribution_template.line", "template_id", string="Ventilation Lines")


class distribution_template_line(models.Model):

    _name = "perso.account.distribution_template.line"

    name        = fields.Char("Description", required=True)
    amount      = fields.Float("Amount", required=True)
    account_id  = fields.Many2one('perso.account', string="Account", required=True)
    template_id = fields.Many2one('perso.account.distribution_template', string="Template")
