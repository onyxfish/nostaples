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
This module holds the L{MainController}, which manages interaction 
between the L{MainModel} and L{MainView}.
"""

import logging

import gtk
from gtkmvc.controller import Controller

from controllers.document import DocumentController
from controllers.page import PageController
from controllers.preferences import PreferencesController
from scanning import ScanningService
from views.preferences import PreferencesView

class MainController(Controller):
    """
    Manages interaction between the L{MainModel} and L{MainView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, model):
        """
        Constructs the MainController, as well as necessary sub-controllers 
        and services.
        """
        Controller.__init__(self, model)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')
        
        # Services
        self.scanning_service = ScanningService()
        
        # Sub-controllers
        self.document_controller = DocumentController(
            model.document_model)

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
        self.adapt('show_toolbar', 'show_toolbar_menu_item')
        self.adapt('show_statusbar', 'show_statusbar_menu_item')
        self.adapt('show_thumbnails', 'show_thumbnails_menu_item')
        
    # USER INTERFACE CALLBACKS
        
    def on_scan_window_destroy(self, window):
        """Exits the application."""
        self.quit()
        
    def on_scan_menu_item_activate(self, menu_item):
        pass
    
    def on_save_as_menu_item_activate(self, menu_item):
        pass
    
    def on_delete_menu_item_activate(self, menu_item):
        pass
    
    def on_insert_scan_menu_item_activate(self, menu_item):
        pass
    
    def on_preferences_menu_item_activate(self, menu_item):
        """Creates and displays a preferences dialog."""
        preferences_controller = PreferencesController(
            self.model.preferences_model)
            
        preferences_view = PreferencesView(
            preferences_controller, self.view)
        
        preferences_view.show()
        
    def on_quit_menu_item_activate(self, menu_item):
        """Exits the application."""
        self.quit()
        
    def on_show_toolbar_menu_item_toggled(self, menu_item):
        """Toggles the visibility of the toolbar."""
        if menu_item.get_active():
            self.view['main_toolbar'].show()
        else:
            self.view['main_toolbar'].hide()
            
    def on_show_statusbar_menu_item_toggled(self, menu_item):
        """Toggles the visibility of the statusbar."""
        if menu_item.get_active():
            self.view['scan_window_statusbar'].show()
        else:
            self.view['scan_window_statusbar'].hide()
            
    def on_show_thumbnails_menu_item_toggled(self, menu_item):
        """Toggles the visibility of the thumbnails pane."""
        self.document_controller.toggle_thumbnails_visible(
            menu_item.get_active())
            
    def on_zoom_in_menu_item_activate(self, menu_item):
        """Zooms the page preview in."""
        self.document_controller.page_controller.zoom_in()
    
    def on_zoom_out_menu_item_activate(self, menu_item):
        """Zooms the page preview out."""
        self.document_controller.page_controller.zoom_out()
    
    def on_zoom_one_to_one_menu_item_activate(self, menu_item):
        """Zooms the page preview to the true size of the scanned image."""
        self.document_controller.page_controller.zoom_one_to_one()
        
    def on_zoom_best_fit_menu_item_activate(self, menu_item):
        """Zooms the page preview to best fit within the preview window."""
        self.document_controller.page_controller.zoom_best_fit()
        
    def on_scan_button_clicked(self, button):
        pass
    
    def on_zoom_in_button_clicked(self, button):
        """Zooms the page preview in."""
        self.document_controller.page_controller.zoom_in()
    
    def on_zoom_out_button_clicked(self, button):
        """Zooms the page preview out."""
        self.document_controller.page_controller.zoom_out()
    
    def on_zoom_one_to_one_button_clicked(self, button):
        """Zooms the page preview to the true size of the scanned image."""
        self.document_controller.page_controller.zoom_one_to_one()
    
    def on_zoom_best_fit_button_clicked(self, button):
        """Zooms the page preview to best fit within the preview window."""
        self.document_controller.page_controller.zoom_best_fit()
    
    # PROPERTY CALLBACKS
    
    # UTILITY METHODS
        
    def quit(self):
        """Exits the application."""
        self.log.debug('Quit.')
        gtk.main_quit()
