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

import nostaples.utils.gui

class DocumentController(Controller):
    """
    Manages interaction between the L{DocumentModel} and
    L{DocumentView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the DocumentsController, as well as necessary
        sub-controllers.
        """
        self.application = application
        Controller.__init__(self, application.get_document_model())
        
        preferences_model = application.get_preferences_model()
        preferences_model.register_observer(self)
        
        status_controller = application.get_status_controller()
        self.status_context = \
            status_controller.get_context_id(self.__class__.__name__)
        
        application.get_document_model().connect(
          'row-changed', self.on_document_model_row_changed)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        view['thumbnails_tree_view'].set_model(
            self.application.get_document_model())
        view['thumbnails_tree_view'].get_selection().connect(
            'changed', self.on_thumbnails_tree_view_selection_changed)
        view['thumbnails_tree_view'].connect(
            'button-press-event', self.on_thumbnails_tree_view_button_press_event)
        
        view['delete_menu_item'].connect(
            "activate", self.on_delete_menu_item_activated)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
    
    def on_thumbnails_tree_view_selection_changed(self, selection):
        """
        Set the current visible page to the be newly selected one.
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        page_controller = self.application.get_page_controller()
        
        selection_iter = selection.get_selected()[1]
        
        if selection_iter:
            page_model = document_model.get_value(selection_iter, 0)
            page_controller.set_current_page_model(page_model)
            document_view['brightness_scale'].set_value(page_model.brightness)
            document_view['contrast_scale'].set_value(page_model.contrast)
            document_view['sharpness_scale'].set_value(page_model.sharpness)
    
    def on_thumbnails_tree_view_button_press_event(self, treeview, event):
        """
        Popup the context menu when the user right-clicks.
        
        Method from U{http://faq.pygtk.org/index.py?req=show&file=faq13.017.htp}.
        """
        document_view = self.application.get_document_view()
        
        if event.button == 3:
            info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if info is not None:
                document_view['thumbnails_context_menu'].popup(
                    None, None, None, event.button, event.time)
            else:
                return True
        
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
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        
        if document_model.manually_updating_row:
            document_model.manually_updating_row = False
        else:
            document_view['thumbnails_tree_view'].get_selection().select_path(path)
            
            # TICKET #49
            # This code causes the application to hang:
#            if document_model.adjust_all_pages:
#                page_model = document_model.get_value(iter, 0)
#                document_model.manually_updating_row = True
#                page_model.set_adjustments(
#                    document_view['brightness_scale'].get_value(),
#                    document_view['contrast_scale'].get_value(),
#                    document_view['sharpness_scale'].get_value())
                
    
    def on_brightness_scale_value_changed(self, widget):
        """
        Sets the brightness of the current page or,
        if "Apply to all pages?" is checked, all scanned
        pages.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        """ 
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        page_model = self.application.get_current_page_model()
        status_controller = self.application.get_status_controller()
        
        if document_model.adjust_all_pages:   
            i = 1
            page_iter = document_model.get_iter_first()
            while page_iter:
                status_controller.push(self.status_context, 'Updating page %i...' % i)
                nostaples.utils.gui.flush_pending_events()
                
                page = document_model.get(page_iter, 0)[0]
                document_model.manually_updating_row = True
                page.brightness = \
                    document_view['brightness_scale'].get_value()
                page_iter = document_model.iter_next(page_iter)
                
                status_controller.pop(self.status_context)
                i = i + 1
        else:
            status_controller.push(self.status_context, 'Updating current page...')
            nostaples.utils.gui.flush_pending_events()
                
            page_model.brightness = \
                document_view['brightness_scale'].get_value()
                
            status_controller.pop(self.status_context)
    
    def on_contrast_scale_value_changed(self, widget):
        """
        Sets the contrast of the current page or,
        if "Apply to all pages?" is checked, all scanned
        pages.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        page_model = self.application.get_current_page_model()
        status_controller = self.application.get_status_controller()
        
        if document_model.adjust_all_pages:      
            i = 1
            page_iter = document_model.get_iter_first()
            while page_iter:
                status_controller.push(self.status_context, 'Updating page %i...' % i)
                nostaples.utils.gui.flush_pending_events()
                
                page = document_model.get(page_iter, 0)[0]
                document_model.manually_updating_row = True
                page.contrast = \
                    document_view['contrast_scale'].get_value()
                page_iter = document_model.iter_next(page_iter)
                
                status_controller.pop(self.status_context)
                i = i + 1
        else:
            status_controller.push(self.status_context, 'Updating current page...')
            nostaples.utils.gui.flush_pending_events()
                
            page_model.contrast = \
                document_view['contrast_scale'].get_value()
                
            status_controller.pop(self.status_context)
    
    def on_sharpness_scale_value_changed(self, widget):
        """
        Sets the sharpness of the current page or,
        if "Apply to all pages?" is checked, all scanned
        pages.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        page_model = self.application.get_current_page_model()
        status_controller = self.application.get_status_controller()
        
        if document_model.adjust_all_pages:      
            i = 1
            page_iter = document_model.get_iter_first()
            while page_iter:
                status_controller.push(self.status_context, 'Updating page %i...' % i)
                nostaples.utils.gui.flush_pending_events()
                
                page = document_model.get(page_iter, 0)[0]
                document_model.manually_updating_row = True
                page.sharpness = \
                    document_view['sharpness_scale'].get_value()
                page_iter = document_model.iter_next(page_iter)
                
                status_controller.pop(self.status_context)
                i = i + 1
        else:
            status_controller.push(self.status_context, 'Updating current page...')
            nostaples.utils.gui.flush_pending_events()
                
            page_model.sharpness = \
                document_view['sharpness_scale'].get_value()
                
            status_controller.pop(self.status_context)
                
    def on_adjust_all_pages_check_toggled(self, checkbox):
        """
        When this box is checked, synchronize all page
        adjustments.
        
        See L{on_document_model_row_changed} for an
        explanation of the voodoo in this method.
        
        # TODO: should set hourglass cursor
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        status_controller = self.application.get_status_controller()
        
        document_model.adjust_all_pages = checkbox.get_active()
        
        if document_model.adjust_all_pages:      
            i = 1
            page_iter = document_model.get_iter_first()
            while page_iter:
                status_controller.push(self.status_context, 'Updating page %i...' % i)
                nostaples.utils.gui.flush_pending_events()
                
                page = document_model.get(page_iter, 0)[0]
                document_model.manually_updating_row = True
                page.set_adjustments(
                    document_view['brightness_scale'].get_value(),
                    document_view['contrast_scale'].get_value(),
                    document_view['sharpness_scale'].get_value())
                page_iter = document_model.iter_next(page_iter)
                
                status_controller.pop(self.status_context)
                i = i + 1
                
    def on_delete_menu_item_activated(self, menu_item):
        """Delete the currently selected page."""
        self.delete_selected()
    
    # PROPERTY CALLBACKS
    
    def property_count_value_change(self, model, old_value, new_value):
        """
        If all pages have been removed/deleted, switch to the null_page
        model for display.
        """
        if new_value == 0:
            self.application.get_page_controller().set_current_page_model(
                self.application.get_null_page_model())
            
    def property_thumbnail_size_value_change(self, model, old_value, new_value):
        """
        Update the size of the thumbnail column and redraw all existing
        thumbnails.
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        
        document_view['thumbnails_column'].set_fixed_width(new_value)
        
        page_iter = document_model.get_iter_first()
        while page_iter:
            page = document_model.get(page_iter, 0)[0]
            page._update_thumbnail_pixbuf()
            page_iter = document_model.iter_next(page_iter)
    
    # PUBLIC METHODS
            
    def toggle_thumbnails_visible(self, visible):
        """Toggle the visibility of the thumbnails view."""
        document_view = self.application.get_document_view()
        
        if visible:
            document_view['thumbnails_scrolled_window'].show()
        else:
            document_view['thumbnails_scrolled_window'].hide()
        
    def toggle_adjustments_visible(self, visible):
        """Toggles the visibility of the adjustments view."""
        document_view = self.application.get_document_view()
        
        if visible:
            document_view['adjustments_alignment'].show()
        else:
            document_view['adjustments_alignment'].hide()
            
    def delete_selected(self):
        """
        Move the selection to the next page and delete the
        currently selected page.
        
        Selection is done here in place of catching the model's row-deleted
        signal, which seems like it I{should} be the proper way to
        do it.  Unfortunantly, when trying to do it that way it
        was impossible to actually select another row as part of
        the event.  This seems to work much more reliably.
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        
        selection_iter = document_view['thumbnails_tree_view'].get_selection().get_selected()[1]
        
        if selection_iter:
            # Get the row element of the path
            row = document_model.get_path(selection_iter)[0]
        
            # Don't switch selections if this is the only page
            if document_model.count == 1:
                pass
            else:
                # Select previous row if deleting the last page
                if row == document_model.count - 1:
                    document_view['thumbnails_tree_view'].get_selection().select_path(row - 1)
                # Otherwise select next row
                else:        
                    document_view['thumbnails_tree_view'].get_selection().select_path(row + 1)            
            
            # Remove the row that was selected when the delete request was made
            document_model.remove(selection_iter)
        else:
            self.log.warn('Method delete_selected was called, but no selection has been made.')
        
    def rotate_counter_clockwise(self, rotate_all):
        """
        Rotate the page counter-clockwise.
        """
        status_controller = self.application.get_status_controller()
        
        if not rotate_all:
            page_model = self.application.get_current_page_model()
            status_controller.push(self.status_context, 'Rotating current page...')
            nostaples.utils.gui.flush_pending_events()
            page_model.rotate_counter_clockwise()
            status_controller.pop(self.status_context)
        else:
            document_model = self.application.get_document_model()
            page_iter = document_model.get_iter_first()
            i = 1
            while page_iter:
                page_model = document_model.get_value(page_iter, 0)
                status_controller.push(self.status_context, 'Rotating page %i...' % i)
                nostaples.utils.gui.flush_pending_events()
                page_model.rotate_counter_clockwise()
                status_controller.pop(self.status_context)
                page_iter = document_model.iter_next(page_iter)
                i = i + 1            
    
    def rotate_clockwise(self, rotate_all):
        """
        Rotate the page clockwise.
        """
        status_controller = self.application.get_status_controller()
        
        if not rotate_all:
            page_model = self.application.get_current_page_model()
            status_controller.push(self.status_context, 'Rotating current page...')
            nostaples.utils.gui.flush_pending_events()
            page_model.rotate_clockwise()
            status_controller.pop(self.status_context)
        else:
            document_model = self.application.get_document_model()
            page_iter = document_model.get_iter_first()
            i = 1
            while page_iter:
                page_model = document_model.get_value(page_iter, 0)
                status_controller.push(self.status_context, 'Rotating page %i...' % i)
                nostaples.utils.gui.flush_pending_events()
                page_model.rotate_clockwise()
                status_controller.pop(self.status_context)
                page_iter = document_model.iter_next(page_iter)
                i = i + 1  
            
    def goto_first_page(self):
        """Select the first scanned page."""
        document_view = self.application.get_document_view()
        
        document_view['thumbnails_tree_view'].get_selection().select_path(0)
    
    def goto_previous_page(self):
        """Select the previous scanned page."""
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        
        iter = document_view['thumbnails_tree_view'].get_selection().get_selected()[1]
        row = document_model.get_path(iter)[0]
        
        if row == 0:
            return
        
        document_view['thumbnails_tree_view'].get_selection().select_path(row - 1)
    
    def goto_next_page(self):
        """Select the next scanned page."""
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        
        iter = document_view['thumbnails_tree_view'].get_selection().get_selected()[1]
        row = document_model.get_path(iter)[0]
        document_view['thumbnails_tree_view'].get_selection().select_path(row + 1)
    
    def goto_last_page(self):
        """
        Select the last scanned page.
        
        Handles invalid paths gracefully without an exception case.
        """
        document_model = self.application.get_document_model()
        document_view = self.application.get_document_view()
        
        document_view['thumbnails_tree_view'].get_selection().select_path(len(document_model) - 1)