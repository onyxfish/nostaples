from types import IntType, StringType, FloatType, BooleanType
import gconf

gconfClient = gconf.client_get_default()

def get_state(path, default):
	'''Gets a key from gconf or, if it is not found, sets a specified default.'''
	value = gconfClient.get(path)
	
	if not value:
		set_gconf_setting(path, default)
		return default
	else:
		if value.type == gconf.VALUE_INT:
			return value.get_int()
		elif value.type == gconf.VALUE_STRING:
			return value.get_string()
		elif value.type == gconf.VALUE_FLOAT:
			return value.get_float()
		elif value.type == gconf.VALUE_BOOL:
			return value.get_bool()
		else:
			raise TypeError, 'Variable type not supported by gconf.'		
			return None				
			
def set_state(path, value):
	'''Sets a key in gconf.'''
	if type(value) is IntType:
		gconfClient.set_int(path, value)
	elif type(value) is StringType:
		gconfClient.set_string(path, value)
	elif type(value) is FloatType:
		gconfClient.set_float(path, value)
	elif type(value) is BooleanType:
		gconfClient.set_bool(path, value)
	else:
		raise TypeError, 'Variable type not supported by gconf.'
		return None