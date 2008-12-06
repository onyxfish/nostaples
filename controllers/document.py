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
        self.page_controller = PageController(self.model.null_page)
        
        self.model.connect(
          'row-changed', self.on_document_model_row_changed)

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
        """
        Set the current visible page to the be newly selected one.
        """
        selection_iter = selection.get_selected()[1]
        
        if selection_iter:
            page_model = self.model.get_value(selection_iter, 0)
            self.page_controller.set_model(page_model)
        else:
            self.page_controller.set_model(self.model.null_page)
        
    def on_document_model_row_changed(self, model, path, iter):
        """
        Select a new rows when they are added.
        
        Per the following FAQ entry, must use row-changed event,
        not row-inserted.
        U{http://faq.pygtk.org/index.py?file=faq13.028.htp&req=show}
        """
        self.view['thumbnails_tree_view'].get_selection().select_path(path)
    
    # PROPERTY CALLBACKS
    
    def property_count_value_change(self, model, old_value, new_value):
        """
        If all pages have been removed/deleted, switch to the null_page
        model for display.
        """
        if new_value == 0:
            self.page_controller.set_model(self.model.null_page)
    
    # UTILITY METHODS
        
    def toggle_thumbnails_visible(self, visible):
        """Toggles the visibility of the thumbnails view."""
        if visible:
            self.view['thumbnails_scrolled_window'].show()
        else:
            self.view['thumbnails_scrolled_window'].hide()
            
    def delete_selected(self):
        """Delete the currently selected page."""
        selection_iter = self.view['thumbnails_tree_view'].get_selection().get_selected()[1]
        
        if selection_iter:
            self.model.remove(selection_iter)
        else:
            self.log.warn('Method delete_selected was called, but no selection has been made.')
            
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