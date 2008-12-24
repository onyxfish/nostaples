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
This module holds the AboutView which exposes the application's
about dialog.
"""

import logging
import os

import gtk
from gtkmvc.view import View

import constants

class AboutView(View):
    """
    Exposes the application's main window.
    """

    def __init__(self, application):
        """Constructs the AboutView."""
        self.application = application
        about_dialog_glade = os.path.join(
            constants.GUI_DIRECTORY, 'about_dialog.glade')
        View.__init__(
            self, self.application.get_about_controller(), 
            about_dialog_glade, 'about_dialog', 
            self.application.get_main_view(), False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.application.get_about_controller().register_view(self)
        
        self.log.debug('Created.')
        
    def run(self):
        """Run this modal dialog."""
        self['about_dialog'].run()