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
This module holds the L{AboutController}, which manages interaction 
between the user and the L{AboutView}.
"""

import logging

from gtkmvc.controller import Controller
from gtkmvc.model import Model

import constants

class AboutController(Controller):
    """
    Manages interaction between the user and the
    L{AboutView}.
    
    See U{http://faq.pygtk.org/index.py?req=show&file=faq10.013.htp}
    for an explanation of all the GTK signal handling voodoo in this
    class.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the AboutController.
        
        Note that About has no model, an empty model is
        passed to the super constructor to avoid assertion
        failures later on.
        """
        self.application = application
        Controller.__init__(self, Model())

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
        
    def on_about_dialog_close(self, dialog):
        """Hide the about dialog."""
        dialog.hide()
        
    def on_about_dialog_response(self, dialog, response):
        """Hide the about dialog."""
        dialog.hide()
        
    def on_about_dialog_delete_event(self, dialog, event):
        """Hide the about dialog."""
        dialog.hide()
        return True
    
    # PUBLIC METHODS
    
    def run(self):
        """Run the modal about dialog."""
        self.application.get_about_view().run()