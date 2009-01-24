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
This module holds the SaveModel, which manages data related to
saving documents.
"""

import logging

from gtkmvc.model import Model

from nostaples import constants

class SaveModel(Model):
    """
    Handles data the metadata associated with saving documents.
    """
    __properties__ = \
    {
        'save_path' : '',
        'title' : '',
        'author' : '',
        'keywords' : '',
        
        'filename' : '',
    }

    def __init__(self, application):
        """
        Constructs the SaveModel.
        """
        self.application = application
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')
        
    def load_state(self):
        """
        Load persisted state from the self.state_manager.
        """
        state_manager = self.application.get_state_manager()
        
        self.save_path = state_manager.init_state(
            'save_path', constants.DEFAULT_SAVE_PATH, 
            self.state_save_path_change)
        
        self.author = state_manager.init_state(
            'author', constants.DEFAULT_AUTHOR, 
            self.state_author_change)
        
    # Property setters
    # (see gtkmvc.support.metaclass_base.py for the origin of these accessors)
        
    def set_prop_save_path(self, value):
        """
        Write state.
        See L{MainModel.set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_save_path
        if old_value == value:
            return
        self._prop_save_path = value
        self.application.get_state_manager()['save_path'] = value
        self.notify_property_value_change(
            'save_path', old_value, value)
        
    def set_prop_author(self, value):
        """
        Write state.
        See L{MainModel.set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_author
        if old_value == value:
            return
        self._prop_author = value
        self.application.get_state_manager()['author'] = value
        self.notify_property_value_change(
            'author', old_value, value)
        
    # STATE CALLBACKS
    
    def state_save_path_change(self):
        """Read state."""
        self.save_path = \
            self.application.get_state_manager()['save_path']
    
    def state_author_change(self):
        """Read state."""
        self.author = \
            self.application.get_state_manager()['author']