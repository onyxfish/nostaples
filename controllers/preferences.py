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
This module holds the L{PreferencesController}, which manages interaction 
between the L{PreferencesModel} and L{PreferencesView}.
"""

import logging

import gtk
from gtkmvc.controller import Controller

from nostaples import constants
from nostaples.utils.gui import read_combobox

class PreferencesController(Controller):
    """
    Manages interaction between the L{PreferencesModel} and 
    L{PreferencesView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the PreferencesController.
        """
        self.application = application
        Controller.__init__(self, application.get_preferences_model())

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def register_adapters(self):
        """
        Registers adapters for property/widget pairs that do not require 
        complex processing.
        """
        pass
    
    # PUBLIC METHODS
    
    def run(self):
        """Run the preferences dialog."""
        preferences_view = self.application.get_preferences_view()
        
        preferences_view.run()
    
    # USER INTERFACE CALLBACKS

    def on_preferences_dialog_response(self, dialog, response):
        """Close the preferences dialog."""
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        preferences_model.preview_mode = \
            read_combobox(preferences_view['preview_mode_combobox'])
        
        preferences_model.thumbnail_size = \
            int(read_combobox(preferences_view['thumbnail_size_combobox']))
        
        preferences_view['preferences_dialog'].hide()