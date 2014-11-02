import openerplib
import ConfigParser
        

def get_server_connection(config_file):
    config = ConfigParser.RawConfigParser({'protocol' : 'xmlrpc', 'port' : 8069})
    config.read(config_file)

    hostname = config.get('Connection', 'hostname')
    database = config.get('Connection', 'database')
    login = config.get('Connection', 'login')
    password = config.get('Connection', 'password')
    protocol = config.get('Connection', 'protocol')
    port = int(config.get('Connection', 'port'))
    return openerplib.get_connection(hostname=hostname, database=database, login=login, password=password, protocol=protocol, port=port)
    
    
def get_version(config_file):
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    version = config.get('tag', 'version')
    return version
    
def get_int_list(config_file, section, parameter):
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    issues = config.get(section, parameter)
    return [int(x) for x in filter(lambda x: x, issues.split(','))]
    

    
        
