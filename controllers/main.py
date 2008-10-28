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
This module holds the controller for the main application view and
model.
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
    TODO
    """
    def __init__(self, model):
        Controller.__init__(self, model)
            
        self.scanning_service = ScanningService()
        
        self.page_controller = PageController(model.blank_page)
        self.document_controller = DocumentController(
            model.document_model)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def register_adapters(self):
        self.adapt('show_toolbar', 'show_toolbar_menu_item')
        self.adapt('show_statusbar', 'show_statusbar_menu_item')
        self.adapt('show_thumbnails', 'show_thumbnails_menu_item')
        
    def quit(self):
        self.log.debug('Quit.')
        gtk.main_quit()
        
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
        if menu_item.get_active():
            self.view['thumbnails_scrolled_window'].show()
        else:
            self.view['thumbnails_scrolled_window'].hide()
        
    def on_scan_button_clicked(self, button):
        pass
