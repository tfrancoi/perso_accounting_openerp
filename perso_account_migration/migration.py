'''
Created on 25 nov. 2014

@author: openerp
'''
from openerp import models, fields, api
from mercurial.transaction import active
from openerp.exceptions import Warning

from openerp.addons.import_base.import_framework import *
from openerp.addons.import_base.mapper import *


class odoo_connection_data(models.TransientModel):
    
    _name = 'perso.account.migration'
    
    @api.multi
    def migrate(self):
        imp = migration_framework(self, self.env.cr, self.env.uid, "Odoo", 'perso.account.migrate', dict(self.env.context))
        imp.launch_import()
    

class migration_framework(import_framework):
    black_list_field = {
        'perso.account' : ['bank_id']                 
    }
    
    tables =  ['perso.bank.account', 
               'perso.account.period', 
               'perso.account', 
               'perso.account.consolidation',
               'perso.account.cash_flow',]

    
    def initialize(self):
        self.connection = self.obj.env['import.odoo.connection'].search([], limit=1)
        self.set_table_list(self.tables)
        print self.connection.name
        
    def _get_field(self, model):
        fields_info = model.fields_get()
        fields = ['id']
        for f_name, f_info in fields_info.items():
            if f_info['type'] in ('many2one', 'many2many'):
                fields.append(f_name + '/id')
            elif f_info['type'] != 'one2many':
                fields.append(f_name)
            #if not 'function' in f_info.keys():
            #    elif f_info['type'] in ('float', 'integer', 'char', 'text', 'date', 'datetime', 'boolean', 'selection'): 
            #        fields.append(f_name)
            #if f_name in self.black_list_field.get(model.model_name, []):
            #    print f_info
        print fields
        return fields
    
    def res_to_dict(self, fields, datas):
        datas = datas['datas']
        res = []
        for data in datas:
            data_dict = {}
            for i, field in enumerate(fields):
                data_dict[field] = data[i]
            res.append(data_dict)
        return res
        
    def get_data(self, table):
        con = self.connection._get_connection()
        obj = con.get_model(table)
        fields = self._get_field(obj)
        ids = obj.search([])
        datas = obj.export_data(ids, fields)
        return self.res_to_dict(fields, datas)

    def _generate_xml_id(self, name, table):
        """
            @param name: name of the object, has to be unique in for a given table
            @param table : table where the record we want generate come from
            @return: a unique xml id for record, the xml_id will be the same given the same table and same name
                     To be used to avoid duplication of data that don't have ids
        """
        return name
 

    def get_mapping(self):
        return {
            'perso.bank.account': { 
                'model' : 'perso.bank.account',
                'dependencies' : [],
                'map' : {
                    'name': 'name',
                }
            },
            'perso.account.period' : {
                'model' : 'perso.account.period',
                'dependencies' : [],
                'map' : {
                    'name' : 'name',
                    'date_start' : 'date_start',
                    'date_end' : 'date_end',
                    'active' : 'active', 
                }
            },
            'perso.account' : {
                'model' : 'perso.account',
                'dependencies' : [],
                'map' : {
                    'name' : 'name',
                    'parent_id/id_parent' : 'parent_id/id',
                    'type' : 'type',
                    'description' : 'description',
                    'budget' : 'budget',
                }
            },
            'perso.account.consolidation' : {
                'model' : 'perso.account.consolidation',
                'dependencies' : ['perso.account'],
                'map' : {
                    'name' : 'name',
                    'description' : 'description',
                    'account_ids/id' : 'account_ids/id',
                }
            },
            'perso.account.cash_flow': {
                'model' : 'perso.account.cash_flow',
                'dependencies' : ['perso.account', 'perso.bank.account'],
                'map' : {
                    'reference' : 'reference',
                    'name' : 'name',
                    'account_id/id' : 'account_id/id', 
                    'bank_id/id' : 'bank_id/id',
                    'value_date' : 'value_date',
                    'transaction_date' : 'transaction_date', 
                    'amount' : 'amount',
                    'distributed' : 'distributed',
                }
            },
        }
        
        

