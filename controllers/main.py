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
        
        self.update_available_scanners()
        
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
        
    def on_rotate_clockwise_menu_item_activate(self, menu_item):
        """Rotates the visible page ninety degress clockwise."""
        self.document_controller.page_controller.rotate_clockwise()
        
    def on_rotate_counter_clockwise_menu_item_activate(self, menu_item):
        """Rotates the visible page ninety degress counter-clockwise."""
        self.document_controller.page_controller.rotate_counter_clockwise()
        
    def on_available_scanner_menu_item_toggled(self, menu_item):
        """Set the active scanner."""
        # TODO: This has not been tested.
        if menu_item.get_active():
            for scanner in self.model.available_scanners:
                if scanner.display_name == menu_item.get_children()[0].get_text():
                    self.model.active_scanner = scanner
                    return
    
    def on_valid_scan_mode_menu_item_toggled(self, menu_item):
        """Sets the active scan mode."""
        if menu_item.get_active():
            self.model.active_scan_mode = \
                menu_item.get_children()[0].get_text()

    def on_valid_scan_resolution_menu_item_toggled(self, menu_item):
        """Sets the active scan resolution."""
        if menu_item.get_active():
            self.model.active_scan_resolution = \
                menu_item.get_children()[0].get_text()
        
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
        
    def on_rotate_clockwise_button_clicked(self, button):
        """Rotates the visible page ninety degress clockwise."""
        self.document_controller.page_controller.rotate_clockwise()
        
    def on_rotate_counter_clockwise_button_clicked(self, button):
        """Rotates the visible page ninety degress counter-clockwise."""
        self.document_controller.page_controller.rotate_counter_clockwise()
    
    # PROPERTY CALLBACKS
    
    def property_available_scanners_value_change(self, model, old_value, new_value):
        """
        Updates the menu listing of available scanners.
        """
        # Clear existing menu items
        for child in self.view['scanner_sub_menu'].get_children():
            self.view['scanner_sub_menu'].remove(child)
        
        first_item = None

        # Note the cast to list() as available_scanners is wrapped in
        # gtkmvc's ObsListWrapper.
        for i in range(len(list(self.model.available_scanners))):
            # The first menu item defines the group
            if i == 0:
                menu_item = gtk.RadioMenuItem(
                    None, self.model.available_scanners[i].display_name)
                first_item = menu_item
            else:
                menu_item = gtk.RadioMenuItem(first_item,
                    self.model.available_scanners[i].display_name)
                
            # Select the first scanner if the previously selected scanner
            # is not in the list
            if i == 0 and self.model.active_scanner not in self.model.available_scanners:
                menu_item.set_active(True)
                self.model.active_scanner = self.model.available_scanners[i]
            
            if self.model.available_scanners[i] == self.model.active_scanner:
                menu_item.set_active(True)
            
            #menu_item.connect('toggled', self.update_scanner_options)
            self.view['scanner_sub_menu'].append(menu_item)
        
        menu_item = gtk.MenuItem('Refresh List')
        #menu_item.connect('activate', self.update_scanner_list)
        self.view['scanner_sub_menu'].append(menu_item)
        
        self.view['scanner_sub_menu'].show_all()
        
        # Emulate the default scanner being toggled
        self.update_valid_scanner_options()
        
        # Notify user if no scanners are connected
#        if selected_item == None:
#            self.gui.statusbar.push(
#                constants.STATUSBAR_SCANNER_STATUS_CONTEXT_ID, 
#                'No scanners available')
#        else:
#            self.gui.statusbar.pop(
#            constants.STATUSBAR_SCANNER_STATUS_CONTEXT_ID)
    
    def property_valid_scan_modes_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan modes for the current scanner.
        """
        # Clear scan modes sub menu
        for child in self.view['scan_mode_sub_menu'].get_children():
            self.view['scan_mode_sub_menu'].remove(child)
        
        # Generate new scan mode menu
        if (len(list(self.model.valid_scan_modes)) == 0):
            self.active_scan_mode = None
            menu_item = gtk.MenuItem("No Scan Modes")
            menu_item.set_sensitive(False)
            self.view['scan_mode_sub_menu'].append(menu_item)
        else:        
            for i in range(len(list(self.model.valid_scan_modes))):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, self.model.valid_scan_modes[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, self.model.valid_scan_modes[i])
                    
                if i == 0 and self.model.active_scan_mode not in self.model.valid_scan_modes:
                    menu_item.set_active(True)
                    self.model.active_scan_mode = self.model.valid_scan_modes[i]
                
                if self.model.valid_scan_modes[i] == self.model.active_scan_mode:
                    menu_item.set_active(True)
                
                menu_item.connect('toggled', self.on_valid_scan_mode_menu_item_toggled)
                self.view['scan_mode_sub_menu'].append(menu_item)
            
        self.view['scan_mode_sub_menu'].show_all()
        
        # Emulate the default scan mode being toggled
        #self.update_scan_mode(selected_item)
        
        # NB: Only do this if everything else has succeeded, 
        # otherwise a crash could repeat everytime the app is started
        #self.state_manager['active_scanner'] = self.active_scanner
    
    def property_valid_scan_resolutions_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan resolutions for the current scanner.
        """
        # Clear scan modes sub menu
        for child in self.view['scan_resolution_sub_menu'].get_children():
            self.view['scan_resolution_sub_menu'].remove(child)
        
        # Generate new scan mode menu
        if (len(list(self.model.valid_scan_resolutions)) == 0):
            self.active_scan_mode = None
            menu_item = gtk.MenuItem("No Scan Resolutions")
            menu_item.set_sensitive(False)
            self.view['scan_resolution_sub_menu'].append(menu_item)
        else:        
            for i in range(len(list(self.model.valid_scan_resolutions))):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, self.model.valid_scan_resolutions[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, self.model.valid_scan_resolutions[i])
                    
                if i == 0 and self.model.active_scan_resolution not in self.model.valid_scan_resolutions:
                    menu_item.set_active(True)
                    self.model.active_scan_resolution = self.model.valid_scan_resolutions[i]
                
                if self.model.valid_scan_resolutions[i] == self.model.active_scan_resolution:
                    menu_item.set_active(True)
                
                menu_item.connect('toggled', self.on_valid_scan_resolution_menu_item_toggled)
                self.view['scan_resolution_sub_menu'].append(menu_item)
            
        self.view['scan_resolution_sub_menu'].show_all()
        
        # Emulate the default scan mode being toggled
        #self.update_scan_mode(selected_item)
        
        # NB: Only do this if everything else has succeeded, 
        # otherwise a crash could repeat everytime the app is started
        #self.state_manager['active_scanner'] = self.active_scanner
        
    def property_active_scanner_value_change(self, model, old_value, new_value):
        pass
        
    # PUBLIC METHODS
        
    def quit(self):
        """Exits the application."""
        self.log.debug('Quit.')
        gtk.main_quit()
        
    def update_available_scanners(self):
        """Retrieve a list of connected scanners ."""
        self.model.available_scanners = \
            self.scanning_service.get_available_scanners()
        
    def update_valid_scanner_options(self):
        """
        Retrieve a list of valid scanner options for the currently selected
        scanner.
        """
        self.model.valid_scan_modes, self.model.valid_scan_resolutions = \
            self.scanning_service.get_scanner_options(
                self.model.active_scanner.sane_name)

    # PRIVATE METHODS