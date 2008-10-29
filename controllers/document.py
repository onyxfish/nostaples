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
This module holds the L{DocumentController}, which manages interaction 
between the L{DocumentModel} and L{DocumentView}.
"""

import logging

import gtk
from gtkmvc.controller import Controller

from controllers.page import PageController

class DocumentController(Controller):
    """
    Manages interaction between the L{DocumentModel} and
    L{DocumentView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, model):
        """
        Constructs the DocumentsController, as well as necessary
        sub-controllers.
        """
        Controller.__init__(self, model)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

        # Sub-controllers
        self.page_controller = PageController(model.blank_page)

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.view['thumbnails_tree_view'].set_model(self.model)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
    
    # PROPERTY CALLBACKS
    
    # UTILITY METHODS
        
    def toggle_thumbnails_visible(self, visible):
        """Toggles the visibility of the thumbnails view."""
        if visible:
            self.view['thumbnails_scrolled_window'].show()
        else:
            self.view['thumbnails_scrolled_window'].hide()
