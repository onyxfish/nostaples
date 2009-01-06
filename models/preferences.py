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
This module holds the PreferencesModel, which manages user settings.
"""

import logging

from gtkmvc.model import Model

import constants

class PreferencesModel(Model):
    """
    Manages user settings.
    """
    __properties__ = \
    {
        'preview_mode' : constants.DEFAULT_PREVIEW_MODE,
        'thumbnail_size' : constants.DEFAULT_THUMBNAIL_SIZE
    }

    def __init__(self, application):
        """
        Constructs the PreferencesModel.
        """
        Model.__init__(self)
        self.application = application
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')
        
    def load_state(self):
        """
        Load persisted state from the self.state_manager.
        """
        state_manager = self.application.get_state_manager()
        
        self.preview_mode = state_manager.init_state(
            'preview_mode', constants.DEFAULT_PREVIEW_MODE, 
            self.state_preview_mode_change)
        
        self.thumbnail_size = state_manager.init_state(
            'thumbnail_size', constants.DEFAULT_THUMBNAIL_SIZE, 
            self.state_thumbnail_size_change)
        
    # Property setters
    # (see gtkmvc.support.metaclass_base.py for the origin of these accessors)
        
    def set_prop_preview_mode(self, value):
        """
        Write state.
        See L{MainModel.set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_preview_mode
        if old_value == value:
            return
        self._prop_preview_mode = value
        self.application.get_state_manager()['preview_mode'] = value
        self.notify_property_value_change(
            'preview_mode', old_value, value)
        
    def set_prop_thumbnail_size(self, value):
        """
        Write state.
        See L{MainModel.set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_thumbnail_size
        if old_value == value:
            return
        self._prop_thumbnail_size = value
        self.application.get_state_manager()['thumbnail_size'] = value
        self.notify_property_value_change(
            'thumbnail_size', old_value, value)
        
    # STATE CALLBACKS
    
    def state_preview_mode_change(self):
        """Read state."""
        self.preview_mode = \
            self.application.get_state_manager()['preview_mode']
    
    def state_thumbnail_size_change(self):
        """Read state."""
        self.thumbnail_size = \
            self.application.get_state_manager()['thumbnail_size']