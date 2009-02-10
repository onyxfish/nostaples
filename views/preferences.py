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
This module holds the PreferencesView which exposes user settings
through a dialog seperate from the main application window.
"""

import logging
import os

import gtk
from gtkmvc.view import View

from nostaples import constants
from nostaples.utils.gui import read_combobox, setup_combobox

class PreferencesView(View):
    """
    Exposes user settings through a dialog seperate from the main
    application window.
    """
    def __init__(self, application):
        """
        Constructs the PreferencesView, including setting up controls that 
        could not be configured in Glade.
        """
        self.application = application
        preferences_dialog_glade = os.path.join(
            constants.GUI_DIRECTORY, 'preferences_dialog.glade')
        View.__init__(
            self, application.get_preferences_controller(), 
            preferences_dialog_glade, 'preferences_dialog', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Can not configure this via constructor do to the multiple
        # root windows in the Main View.
        self['preferences_dialog'].set_transient_for(application.get_main_view()['scan_window'])
        
        setup_combobox(
            self['preview_mode_combobox'],
            constants.PREVIEW_MODES_LIST, 
            application.get_preferences_model().preview_mode)
        
        setup_combobox(
            self['thumbnail_size_combobox'],
            constants.THUMBNAIL_SIZE_LIST, 
            application.get_preferences_model().thumbnail_size)
        
        application.get_preferences_controller().register_view(self)
        
        self.log.debug('Created.')
        
    def run(self):
        """Run the modal preferences dialog."""
        self['preferences_dialog'].run()