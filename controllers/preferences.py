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

from utils.gui import read_combobox

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
    
    # USER INTERFACE CALLBACKS

    def on_preferences_dialog_close(self, dialog):
        """Exits the preferences dialog."""
        self.close()
        
    def on_preview_mode_combobox_changed(self, combobox):
        """Registers changes in the preview rendering mode."""
        self.model.preview_mode = read_combobox(
            self.view['preview_mode_combobox'])
            
        # TODO: where and when does display get updated?
    
    def on_preferences_close_button_clicked(self, button):
        """Exits the preferences dialog."""
        self.close()
    
    # PROPERTY CALLBACKS
    
    # UTILITY METHODS
    
    def close(self):
        """Close the preferences dialog."""
        self.view.hide()
