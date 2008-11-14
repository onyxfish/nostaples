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
from models.page import PageModel

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
        # TODO: Temp (should load document_model.null_page)
        self.page_model = PageModel(path='test.pnm', resolution=75)
        self.page_model2 = PageModel(path='test.pnm', resolution=75)
        self.model.append(self.page_model)
        self.model.append(self.page_model2)
        self.page_controller = PageController(model[0][0])

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.view['thumbnails_tree_view'].set_model(self.model)
        self.view['thumbnails_tree_view'].get_selection().connect(
          'changed', self.on_thumbnails_tree_view_selection_changed)
        
        # TODO: temp?
        self.view['thumbnails_tree_view'].get_selection().select_path(0)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
    
    def on_thumbnails_tree_view_selection_changed(self, selection):
        selection_iter = selection.get_selected()[1]
        
        if not selection_iter:
            return
        
        page_model = self.model.get_value(selection_iter, 0)
        self.page_controller.set_model(page_model)
    
    # PROPERTY CALLBACKS
    
    # UTILITY METHODS
        
    def toggle_thumbnails_visible(self, visible):
        """Toggles the visibility of the thumbnails view."""
        if visible:
            self.view['thumbnails_scrolled_window'].show()
        else:
            self.view['thumbnails_scrolled_window'].hide()
            
    def goto_first_page(self):
        """Select the first scanned page."""
        self.view['thumbnails_tree_view'].get_selection().select_path(0)
    
    def goto_previous_page(self):
        """Select the previous scanned page."""
        iter = self.view['thumbnails_tree_view'].get_selection().get_selected()[1]
        row = self.model.get_path(iter)[0]
        
        if row == 0:
            return
        
        self.view['thumbnails_tree_view'].get_selection().select_path(row - 1)
    
    def goto_next_page(self):
        """Select the next scanned page."""
        iter = self.view['thumbnails_tree_view'].get_selection().get_selected()[1]
        row = self.model.get_path(iter)[0]
        self.view['thumbnails_tree_view'].get_selection().select_path(row + 1)
    
    def goto_last_page(self):
        """
        Select the last scanned page.
        
        Handles invalid paths gracefully without an exception case.
        """        
        self.view['thumbnails_tree_view'].get_selection().select_path(len(self.model) - 1)