#!/usr/bin/python

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

"""
This module holds a utility class which manages persisting state to
a gconf backend and processing callbacks when that state has changed.

Note that a module-scoped StateManager variable is declared at the
end of this module so that can be effectively used as a Singleton.
"""

import logging
from types import IntType, StringType, FloatType, BooleanType

import gconf

import constants

class GConfState():
    '''
    A simple class to hold the data for a state that is managed
    by the L{GConfStateManager}.
    '''

    def __init__(self, name, value, callback):
        '''
        Initializes a managed state with the specified settings.
        '''
        self.name = name
        self.path = '/'.join([constants.GCONF_DIRECTORY, self.name])
        self.value = value
        self.callback = callback
        self.python_type = type(value)
        
        # Store both the Python type and the GConf type to save converting
        # later on.
        if self.python_type is IntType:
            self.gconf_type = gconf.VALUE_INT
        elif self.python_type is StringType:
            self.gconf_type = gconf.VALUE_STRING
        elif self.python_type is FloatType:
            self.gconf_type = gconf.VALUE_FLOAT
        elif self.python_type is BooleanType:
            self.gconf_type = gconf.VALUE_BOOL
        else:
            raise TypeError

class GConfStateManager(dict):
    '''
    Persists application settings using GNOME's GConf configuration
    system.  Handles type validation automatically.
    
    TODO: use pygtkmvc base classes instead of rolling custom observor pattern
        and property management
    TODO: should really observe models and in turn be observed by them,
        rather than having them do both parts.  Right?
    '''
    
    def __init__(self):
        '''
        Grabs a reference to the default GConf client and 
        initializes a dictionary of states that will be managed.
        
        The dictionary is formatted this way:
        states["state_name"] = GConfState()
        '''
        self.states = {}
        
        self.gconf_client = gconf.client_get_default()
        self.gconf_client.add_dir(
            constants.GCONF_DIRECTORY, gconf.CLIENT_PRELOAD_ONELEVEL)
        
    def init_state(self, state_name, default_value, callback=None):
        '''
        Sets up a managed copy of a state.  Checks if a value is already
        stored in GConf and if so loads it into the managed copy, otherwise
        sets a default value in both places.  Also sets a reference to a 
        default callback, which will do basic validation before calling 
        the state callback.
        '''
        dict.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Check that a state is not initialized twice
        if state_name in self.states.keys():
            self.log.error(
                'State %s already exists in state manager.' % state_name)
            return
        
        # Create a new managed state
        try:
            state = GConfState(state_name, default_value, callback)
            self.states[state_name] = state
        except TypeError:
            # This error is rethrown so it can be handled at the interface level
            # as it is probably breaking and should absolutely never happen
            self.log.error(
                'Type %s is not supported GConf.' % str(self.python_type))
            raise            
    
        # Load any value already stored in GConf
        stored_value = self.gconf_client.get(state.path)
        
        if stored_value:
            if state.python_type is IntType:
                state.value = stored_value.get_int()
            elif state.python_type is StringType:
                state.value = stored_value.get_string()
            elif state.python_type is FloatType:
                state.value = stored_value.get_float()
            elif state.python_type is BooleanType:
                state.value = stored_value.get_bool()
            else:
                # It should not be possible to get here due to previous
                # error-checking.
                self.log.error(
                    'Type %s is not supported GConf.' % str(state.python_type))
                raise TypeError
        # If there was not a state stored, then set the default
        else:
            if state.python_type is IntType:
                self.gconf_client.set_int(state.path, default_value)
            elif state.python_type is StringType:
                self.gconf_client.set_string(state.path, default_value)
            elif state.python_type is FloatType:
                self.gconf_client.set_float(state.path, default_value)
            elif state.python_type is BooleanType:
                self.gconf_client.set_bool(state.path, default_value)
            else:
                # It should not be possible to get here due to previous
                # error-checking.
                self.log.error(
                    'Type %s is not supported GConf.' % str(state.python_type))
                raise TypeError
        
        # Add generic state callback
        self.gconf_client.notify_add(state.path, self.__gconf_value_changed)
        
        # Return either the stored value or the default value
        return state.value
    
    def __getitem__(self, state_name):
        '''
        Retrieves the value from the managed copy of a state.  This
        managed copy is kept updated with every call to L{__setitem__}
        and L{__gconf_value_changed} so it should always be in sync 
        with the GConf database.
        '''
        try:
            state = self.states[state_name]
        except IndexError:
            # When a state has not been initialized raise a breaking error
            self.log.error(
                'State %s does not exist in the state manager.' % state_name)
            raise KeyError

        return state.value
    
    def __setitem__(self, state_name, new_value):
        '''
        Sets a value in both the managed copy of a state and the GConf
        database.
        '''
        try:
            state = self.states[state_name]
        except IndexError:
            # When a state has not been initialized raise a breaking error
            self.log.error(
                'State %s does not exist in the state manager.' % state_name)
            raise KeyError
            
        # If the value has not changed then don't bother updating GConf
        if new_value == state.value:
            return
        
        # Validate that the new value matches the type of the value
        # originally specified for this state.
        if type(new_value) != state.python_type:
            self.log.error(
                'Type %s is not the correct type for state %s. \
                It should be %s.' % 
                    str(type(new_value)), state_name, str(state.python_type))
            # When a wrong type is assigned raise a breaking error
            raise TypeError
        
        self.log.debug(
            'Updating state %s with new value %s.' %
                (state_name, str(new_value)))
            
        state.value = new_value
                    
        if state.python_type is IntType:
            self.gconf_client.set_int(state.path, new_value)
        elif state.python_type is StringType:
            self.gconf_client.set_string(state.path, new_value)
        elif state.python_type is FloatType:
            self.gconf_client.set_float(state.path, new_value)
        elif state.python_type is BooleanType:
            self.gconf_client.set_bool(state.path, new_value)
        else:
            # It should not be possible to get here due to error-checking
            # when the state was initialized.
            self.log.error(
                'Type %s is not supported GConf.' % str(state.python_type))
            raise TypeError
        
    def __gconf_value_changed(self, client, connection_id, entry, error):
        '''
        Generic callback that handles updates made to the GConf
        database.  After checking, calls the state callback if one
        has been specified.
        '''
        state_name = entry.get_key().split('/')[-1]
        
        # Get the referenced state
        try:
            state = self.states[state_name]
        except IndexError:
            # Treat this as a non-breaking error since it should be impossible
            # anyway.
            self.log.error(
                'A callback was handled for non-initialized state %s.  \
                (How could this ever happen?)' % state_name)
            return
        
        # Get the modified value (in GConfValue format at this point)
        new_value = entry.get_value()
        
        # Verify that the GConf value is of the expected type, if not then
        # a third-party was mucking with our config settings and we need
        # to revert to the previous setting.
        if new_value.type is not state.gconf_type:
            # ERROR: not the correct type, reset old value
            self.log.error(
                'An invalid value was set for state %s.  \
                The state has been reset to its previous value.' % state_name)
            self[state_name] = state.value
            return
        
        # Get a proper, Python-typed version of the GConfValue
        if state.python_type is IntType:
            new_value_typed = new_value.get_int()
        elif state.python_type is StringType:
            new_value_typed = new_value.get_string()
        elif state.python_type is FloatType:
            new_value_typed = new_value.get_float()
        elif state.python_type is BooleanType:
            new_value_typed = new_value.get_bool()
        else:
            # It should not be possible to get here due to prior error-checking
            self.log.error(
                'Type %s is not supported GConf.' % str(state.python_type))
            raise TypeError   
            
        # If the value has not changed then the callback was triggered
        # by a call to L{__setitem__} in this application.  That method
        # should have updated the managed copy, so we should be safe
        # to exit without updating.  (Updating again could lead to an
        # endless loop.)
        if new_value_typed == state.value:
            return
        
        state.value = new_value_typed
        
        self.log.debug(
            'An external operation has updated state %s with value %s.' %
                (state_name, str(new_value_typed)))
        
        # Call the state callback if one was specified during init_state()
        if state.callback != None:
            state.callback()

# Instance shared across all importing modules 
StateManager = GConfStateManager()
