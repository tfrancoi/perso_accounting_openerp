'''
Created on 1 nov. 2014

@author: openerp
'''
import conf_lib

model_list = [
    'perso.bank.account',
    'perso.account.period',
    'perso.account',
    "perso.account.consolidation",
    "perso.account.cash_flow",
]

black_list_field = {
   'perso.account' : ['bank_id']                 
                    
}

def export_object(con, object_name):
    model = con.get_model(object_name)
    fields_info = model.fields_get()
    fields = ['id']
    for f_name, f_info in fields_info.items():
        if not 'function' in f_info.keys():
            if f_info['type'] in ('many2one', 'many2many'):
                fields.append(f_name + '/id')
            elif f_info['type'] in ('float', 'integer', 'char', 'text', 'date', 'datetime', 'boolean', 'selection'): 
                fields.append(f_name)
        if f_name in black_list_field.get(object_name, []):
            print f_info
    print fields
    ids = model.search([])
    datas = model.export_data(ids, fields)
    return fields, datas['datas']

def import_object(con, object_name, fields, datas):
    model = con.get_model(object_name)
    for d in datas:
        print d
        model.load(fields, [d])

con = conf_lib.get_server_connection("connection.conf")
des_con = conf_lib.get_server_connection("connection_dest.conf")
for model in model_list:
    print "model :", model
    fields, datas = export_object(con, model)
    import_object(des_con, model, fields, datas)
 
