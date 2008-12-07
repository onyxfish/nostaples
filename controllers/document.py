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
        
        # TODO: when a new row is added, if adjust_all is checked
        # the current scale values should be applied to it.
        if selection_iter:
            page_model = self.model.get_value(selection_iter, 0)
            self.page_controller.set_model(page_model)
            self.view['brightness_scale'].set_value(page_model.brightness)
            self.view['contrast_scale'].set_value(page_model.contrast)
            self.view['sharpness_scale'].set_value(page_model.sharpness)
        else:
            self.page_controller.set_model(self.model.null_page)
        
    def on_document_model_row_changed(self, model, path, iter):
        """
        Select a new rows when they are added.
        
        Per the following FAQ entry, must use row-changed event,
        not row-inserted.
        U{http://faq.pygtk.org/index.py?file=faq13.028.htp&req=show}
        
        Regarding the voodoo in this method:
        Whenever an adjustment causes page_model.thumbnail_pixbuf
        to be updated, the treeview emits a row-changed signal.
        If this method is allowed to handle those changes, then the
        change will be treated as a new row and it will be
        selected.  This causes all sorts of unusual problems. To
        avoid this, all changes to a page_model that will cause
        thumbnail_pixbuf to be updated should be preceeded by
        setting the manually_updating_row flag so that this event
        can bypass them appropriately.
        """
        if self.model.manually_updating_row:
            self.model.manually_updating_row = False
        else:
            self.view['thumbnails_tree_view'].get_selection().select_path(path)
    
    def on_brightness_scale_value_changed(self, widget):
        """
        Sets the brightness of the current page or,
        if "Apply to all pages?" is checked, all scanned
        pages.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        """
        if self.model.adjust_all_pages:
            page_iter = self.model.get_iter_first()
            while page_iter:
                page = self.model.get(page_iter, 0)[0]
                self.model.manually_updating_row = True
                page.brightness = \
                    self.view['brightness_scale'].get_value()
                page_iter = self.model.iter_next(page_iter)
        else:
            self.page_controller.model.brightness = \
                self.view['brightness_scale'].get_value()
    
    def on_contrast_scale_value_changed(self, widget):
        """
        Sets the contrast of the current page or,
        if "Apply to all pages?" is checked, all scanned
        pages.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        """
        if self.model.adjust_all_pages:
            page_iter = self.model.get_iter_first()
            while page_iter:
                page = self.model.get(page_iter, 0)[0]
                self.model.manually_updating_row = True
                page.contrast = \
                    self.view['contrast_scale'].get_value()
                page_iter = self.model.iter_next(page_iter)
        else:
            self.page_controller.model.contrast = \
                self.view['contrast_scale'].get_value()
    
    def on_sharpness_scale_value_changed(self, widget):
        """
        Sets the sharpness of the current page or,
        if "Apply to all pages?" is checked, all scanned
        pages.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        """
        if self.model.adjust_all_pages:
            page_iter = self.model.get_iter_first()
            while page_iter:
                page = self.model.get(page_iter, 0)[0]
                self.model.manually_updating_row = True
                page.sharpness = \
                    self.view['sharpness_scale'].get_value()
                page_iter = self.model.iter_next(page_iter)
        else:
            self.page_controller.model.sharpness = \
                self.view['sharpness_scale'].get_value()
                
    def on_adjust_all_pages_check_toggled(self, checkbox):
        """
        When this box is checked, synchronize all page
        adjustments.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        
        # TODO: should set hourglass cursor
        """
        self.model.adjust_all_pages = checkbox.get_active()
        
        if self.model.adjust_all_pages:
            page_iter = self.model.get_iter_first()
            while page_iter:
                page = self.model.get(page_iter, 0)[0]
                self.model.manually_updating_row = True
                page.set_adjustments(
                    self.view['brightness_scale'].get_value(),
                    self.view['contrast_scale'].get_value(),
                    self.view['sharpness_scale'].get_value())
                page_iter = self.model.iter_next(page_iter)
    
    # PROPERTY CALLBACKS
    
    def property_count_value_change(self, model, old_value, new_value):
        """
        If all pages have been removed/deleted, switch to the null_page
        model for display.
        """
        if new_value == 0:
            self.page_controller.set_model(self.model.null_page)
            self.view.set_adjustments_sensitive(False)
        else:
            self.view.set_adjustments_sensitive(True)
    
    # UTILITY METHODS
        
    def toggle_thumbnails_visible(self, visible):
        """Toggles the visibility of the thumbnails view."""
        if visible:
            self.view['thumbnails_scrolled_window'].show()
        else:
            self.view['thumbnails_scrolled_window'].hide()
        
    def toggle_adjustments_visible(self, visible):
        """Toggles the visibility of the adjustments view."""
        if visible:
            self.view['adjustments_alignment'].show()
        else:
            self.view['adjustments_alignment'].hide()
            
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