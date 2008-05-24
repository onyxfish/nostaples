#!/usr/env/python

#~ This file is part of NoStaples.

#~ NoStaples is free software: you can redistribute it and/or modify
#~ it under the terms of the GNU General Public License as published by
#~ the Free Software Foundation, either version 3 of the License, or
#~ (at your option) any later version.

#~ NoStaples is distributed in the hope that it will be useful,
#~ but WITHOUT ANY WARRANTY; without even the implied warranty of
#~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#~ GNU General Public License for more details.

#~ You should have received a copy of the GNU General Public License
#~ along with NoStaples.  If not, see <http://www.gnu.org/licenses/>.

from types import IntType, StringType, FloatType, BooleanType
import gconf

GCONF_FOLDER = "/apps/nostaples"

class GConfStateEngine():
	'''An engine to preserve program settings between runs that is based on GNOME's gconf.'''
	
	def __init__(self):
		self.states = {}
		self.callbacks = {}
		self.gconfClient = gconf.client_get_default()
		self.gconfClient.add_dir(GCONF_FOLDER, gconf.CLIENT_PRELOAD_NONE)
		
	def __get_gconf_path(self, state):
		return '/'.join([GCONF_FOLDER, state])
		
	def __get_state_from_path(self, path):
		return path.split('/')[-1]
		
	def init_state(self, state, default, callback=None):
		path = self.__get_gconf_path(state)
		value = self.gconfClient.get(path)
		
		if not value:
			self.set_state(state, default)
			self.states[state] = default
		else:
			if value.type == gconf.VALUE_INT:
				self.states[state] = value.get_int()
			elif value.type == gconf.VALUE_STRING:
				self.states[state] = value.get_string()
			elif value.type == gconf.VALUE_FLOAT:
				self.states[state] = value.get_float()
			elif value.type == gconf.VALUE_BOOL:
				self.states[state] = value.get_bool()
			else:
				raise TypeError, 'Variable type not supported.'
				
		self.callbacks[state] = callback
		self.gconfClient.notify_add(path, self.__notify_state)
	
	def get_state(self, state):
		assert state in self.states, 'State "%s" has not been initialized with a call to init_state()'
		return self.states[state]
		
	def set_state(self, state, value):
		assert state in self.states, 'State "%s" has not been initialized with a call to init_state()'
		
		if type(value) is IntType:
			self.gconfClient.set_int(self.__get_gconf_path(state), value)
		elif type(value) is StringType:
			self.gconfClient.set_string(self.__get_gconf_path(state), value)
		elif type(value) is FloatType:
			self.gconfClient.set_float(self.__get_gconf_path(state), value)
		elif type(value) is BooleanType:
			self.gconfClient.set_bool(self.__get_gconf_path(state), value)
		else:
			raise TypeError, 'Variable type not supported by gconf.'
			
		self.states[state] = value
		
	def __notify_state(self, client, connectionId, entry, error):		
		state = self.__get_state_from_path(entry.get_key())
		value = entry.get_value()
		
		if value.type == gconf.VALUE_INT:
			self.states[state] = value.get_int()
		elif value.type == gconf.VALUE_STRING:
			self.states[state] = value.get_string()
		elif value.type == gconf.VALUE_FLOAT:
			self.states[state] = value.get_float()
		elif value.type == gconf.VALUE_BOOL:
			self.states[state] = value.get_bool()
		else:
			raise TypeError, 'Variable type not supported.'
			
		if self.callbacks[state]:
			self.callbacks[state]()