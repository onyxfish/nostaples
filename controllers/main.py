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

import commands
import logging
import os
import re
import threading

import gobject
import gtk
from gtkmvc.controller import Controller

from controllers.document import DocumentController
from controllers.page import PageController
from controllers.preferences import PreferencesController
from controllers.save import SaveController
from models.page import PageModel
from models.scanner import ScannerModel
from utils.scanning import *
from views.preferences import PreferencesView
from views.save import SaveView

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
        
        # Sub-controllers
        
        self.document_controller = DocumentController(
            self.model.document_model)

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        # Load persistent state from backend
        self.model.load_state()
        
        self._update_available_scanners()
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def register_adapters(self):
        """
        Registers adapters for property/widget pairs that do not require 
        complex processing.
        """
        self.adapt('show_toolbar', 'show_toolbar_menu_item')
        self.adapt('show_statusbar', 'show_statusbar_menu_item')
        self.adapt('show_thumbnails', 'show_thumbnails_menu_item')
        self.adapt('show_adjustments', 'show_adjustments_menu_item')        
        self.log.debug('Adapters registered.')
        
    # USER INTERFACE CALLBACKS
        
    def on_scan_window_destroy(self, window):
        """Exits the application."""
        self.quit()
        
    def on_scan_menu_item_activate(self, menu_item):
        """Scan a page into the current document."""
        self._scan()
    
    def on_save_as_menu_item_activate(self, menu_item):
        """Saves the current document to a file."""
        self._save_as()
    
    def on_delete_menu_item_activate(self, menu_item):
        self.document_controller.delete_selected()
    
    def on_insert_scan_menu_item_activate(self, menu_item):
        """Scan a page into the current document."""
        self._scan()
    
    def on_preferences_menu_item_activate(self, menu_item):
        """Creates and displays a preferences dialog."""
        self._show_preferences()
        
    def on_quit_menu_item_activate(self, menu_item):
        """Exits the application."""
        self.quit()
            
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
        
    def on_rotate_all_pages_menu_item_toggled(self, menu_item):
        """TODO"""
        pass
        
    def on_available_scanner_menu_item_toggled(self, menu_item):
        """Set the active scanner."""
        # TODO: This has not been tested.
        if menu_item.get_active():
            for scanner in self.model.available_scanners:
                if scanner[0] == menu_item.get_children()[0].get_text():
                    self.model.active_scanner = scanner
                    return
                
    def on_refresh_available_scanners_menu_item_activate(self, menu_item):
        """Refresh the list of connected scanners from SANE."""
        self._update_available_scanners()
                
    def on_go_first_menu_item_activate(self, menu_item):
        """Selects the first scanned page."""
        self.document_controller.goto_first_page()
        
    def on_go_previous_menu_item_activate(self, menu_item):
        """Selects the scanned page before to the currently selected one."""
        self.document_controller.goto_previous_page()
    
    def on_go_next_menu_item_activate(self, menu_item):
        """Selects the scanned page after to the currently selected one."""
        self.document_controller.goto_next_page()
    
    def on_go_last_menu_item_activate(self, menu_item):
        """Selects the last scanned page."""
        self.document_controller.goto_last_page()
        
    def on_scan_button_clicked(self, button):
        """Scan a page into the current document."""
        self._scan()
        
    def on_save_as_button_clicked(self, button):
        """Saves the current document to a file."""
        self._save_as()
    
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
        
    def on_valid_mode_menu_item_toggled(self, menu_item):
        """Sets the active scan mode."""
        if menu_item.get_active():
            self.model.active_mode = \
                menu_item.get_children()[0].get_text()

    def on_valid_resolution_menu_item_toggled(self, menu_item):
        """Sets the active scan resolution."""
        if menu_item.get_active():
            self.model.active_resolution = \
                menu_item.get_children()[0].get_text() 
        
    def on_go_first_button_clicked(self, button):
        """Selects the first scanned page."""
        self.document_controller.goto_first_page()
        
    def on_go_previous_button_clicked(self, button):
        """Selects the scanned page before to the currently selected one."""
        self.document_controller.goto_previous_page()
    
    def on_go_next_button_clicked(self, button):
        """Selects the scanned page after to the currently selected one."""
        self.document_controller.goto_next_page()
    
    def on_go_last_button_clicked(self, button):
        """Selects the last scanned page."""
        self.document_controller.goto_last_page()
    
    # PROPERTY CALLBACKS
    
    def property_show_toolbar_value_change(self, model, old_value, new_value):
        """Update the visibility of the toolbar."""
        menu_item = self.view['show_toolbar_menu_item']
        menu_item.set_active(new_value)
        
        if new_value:
            self.view['main_toolbar'].show()
        else:
            self.view['main_toolbar'].hide()
    
    def property_show_statusbar_value_change(self, model, old_value, new_value):
        """Update the visibility of the statusbar."""
        menu_item = self.view['show_statusbar_menu_item']
        menu_item.set_active(new_value)
        
        if new_value:
            self.view['scan_window_statusbar'].show()
        else:
            self.view['scan_window_statusbar'].hide()

    def property_show_thumbnails_value_change(self, model, old_value, new_value):
        """Update the visibility of the thumbnails."""
        menu_item = self.view['show_thumbnails_menu_item']
        menu_item.set_active(new_value)
        
        self.document_controller.toggle_thumbnails_visible(new_value)

    def property_show_adjustments_value_change(self, model, old_value, new_value):
        """Update the visibility of the adjustments controls."""
        menu_item = self.view['show_adjustments_menu_item']
        menu_item.set_active(new_value)
        
        self.document_controller.toggle_adjustments_visible(new_value)       
            
    def property_available_scanners_value_change(self, model, old_value, new_value):
        """
        Updates the menu listing of available scanners.
        """
        # Clear existing menu items
        for child in self.view['scanner_sub_menu'].get_children():
            self.view['scanner_sub_menu'].remove(child)
        
        if len(list(self.model.available_scanners)) == 0:
            self.model.active_scanner = None
            menu_item = gtk.MenuItem('No Scanners Connected')
            menu_item.set_sensitive(False)
            self.view['scanner_sub_menu'].append(menu_item)
        else:
            first_item = None
    
            # Note the cast to list() as available_scanners is wrapped in
            # gtkmvc's ObsListWrapper.
            for i in range(len(list(self.model.available_scanners))):
                # The first menu item defines the group
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, self.model.available_scanners[i][0])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(first_item,
                        self.model.available_scanners[i][0])
                    
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
        menu_item.connect('activate', self.on_refresh_available_scanners_menu_item_activate)
        self.view['scanner_sub_menu'].append(menu_item)
        
        self.view['scanner_sub_menu'].show_all()
        
        # Notify user if no scanners are connected
#        if selected_item == None:
#            self.gui.statusbar.push(
#                constants.STATUSBAR_SCANNER_STATUS_CONTEXT_ID, 
#                'No scanners available')
#        else:
#            self.gui.statusbar.pop(
#            constants.STATUSBAR_SCANNER_STATUS_CONTEXT_ID)
        
    def property_active_scanner_value_change(self, model, old_value, new_value):
        """TODO"""
        self._update_scanner_options()
        pass
        
    def property_valid_modes_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan modes for the current scanner.
        """
        self._clear_scan_modes_sub_menu()
        
        # Generate new scan mode menu
        if (len(list(self.model.valid_modes)) == 0):
            self.model.active_scan_mode = None
            menu_item = gtk.MenuItem("No Scan Modes")
            menu_item.set_sensitive(False)
            self.view['scan_mode_sub_menu'].append(menu_item)
        else:        
            for i in range(len(list(self.model.valid_modes))):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, self.model.valid_modes[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, self.model.valid_modes[i])
                    
                if i == 0 and self.model.active_mode not in self.model.valid_modes:
                    menu_item.set_active(True)
                    self.model.active_mode = self.model.valid_modes[i]
                
                if self.model.valid_modes[i] == self.model.active_mode:
                    menu_item.set_active(True)
                
                menu_item.connect('toggled', self.on_valid_mode_menu_item_toggled)
                self.view['scan_mode_sub_menu'].append(menu_item)
            
        self.view['scan_mode_sub_menu'].show_all()
        
        # NB: Only do this if everything else has succeeded, 
        # otherwise a crash could repeat everytime the app is started
        #self.state_manager['active_scanner'] = self.active_scanner
    
    def property_valid_resolutions_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan resolutions for the current scanner.
        """
        self._clear_scan_resolutions_sub_menu()
        
        # Generate new scan mode menu
        if (len(list(self.model.valid_resolutions)) == 0):
            self.model.active_resolution = None
            menu_item = gtk.MenuItem("No Scan Resolutions")
            menu_item.set_sensitive(False)
            self.view['scan_resolution_sub_menu'].append(menu_item)
        else:        
            for i in range(len(list(self.model.valid_resolutions))):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, self.model.valid_resolutions[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, self.model.valid_resolutions[i])
                    
                if i == 0 and self.model.active_resolution not in self.model.valid_resolutions:
                    menu_item.set_active(True)
                    self.model.active_resolution = self.model.valid_resolutions[i]
                
                if self.model.valid_resolutions[i] == self.model.active_resolution:
                    menu_item.set_active(True)
                
                menu_item.connect('toggled', self.on_valid_resolution_menu_item_toggled)
                self.view['scan_resolution_sub_menu'].append(menu_item)
            
        self.view['scan_resolution_sub_menu'].show_all()
        
        # NB: Only do this if everything else has succeeded, 
        # otherwise a crash could repeat everytime the app is started
        #self.state_manager['active_scanner'] = self.active_scanner        
        
    def property_is_scanner_in_use_value_change(self, model, old_value, new_value):
        """
        Disable scan controls if the scanner is being accessed, renable if it is not.
        """
        # TODO: only if doc not empty and scanner options parsed
        self.view.set_scan_controls_sensitive(not new_value)
        
    def property_is_document_empty_value_change(self, model, old_value, new_value):
        """
        Disable file and page manipulation controls if no pages have been scanned.
        """
        if self.view:
            self.view.set_file_controls_sensitive(not new_value)
            self.view.set_delete_controls_sensitive(not new_value)
            self.view.set_zoom_controls_sensitive(not new_value)
            self.view.set_adjustment_controls_sensitive(not new_value)        
            self.view.set_navigation_controls_sensitive(not new_value)
    
    # THREAD CALLBACKS
    
    def on_scan_succeeded(self, scanning_thread, filename):
        """Append the new page to the current document."""
        new_page = PageModel(filename, int(self.model.active_resolution))
        self.model.document_model.append(new_page)
        self.model.is_scanner_in_use = False
    
    def on_scan_failed(self, scanning_thread):
        # TODO: check if the scanner has been disconnected
        # TODO: docstring
        self.model.is_scanner_in_use = False
        
    def on_update_available_scanners_thread_finished(self, update_thread, scanner_list):
        """Set the new list of available scanners."""
        self.model.available_scanners = scanner_list
        self.model.is_scanner_in_use = False
            
    def on_update_scanner_options_thread_finished(self, update_thread, mode_list, resolution_list):
        """
        Update the mode and resolution lists and rark that
        the scanner is no longer in use.
        """
        self.model.valid_modes = mode_list
        self.model.valid_resolutions = resolution_list
        
    # PUBLIC METHODS
        
    def quit(self):
        """Exits the application."""
        self.log.debug('Quit.')
        gtk.main_quit()

    # PRIVATE METHODS

    def _save_as(self):
        """
        Save the current document.
        """
        save_controller = SaveController(
            self.model.save_model,
            self.model.document_model)
            
        save_view = SaveView(
            save_controller, self.view)
        
        save_controller.run()
        
    def _show_preferences(self):
        """
        Shows the Preferences dialog.
        """
        preferences_controller = PreferencesController(
            self.model.preferences_model)
            
        preferences_view = PreferencesView(
            preferences_controller, self.view)
        
        preferences_view.show()
    
    def _scan(self):
        """
        Begin a scan.
        """
        self.model.is_scanner_in_use = True
        scanning_thread = ScanningThread(self.model)
        scanning_thread.connect("succeeded", self.on_scan_succeeded)
        scanning_thread.connect("failed", self.on_scan_failed)
        scanning_thread.start()
            
    def _update_available_scanners(self):
        """
        Start a new update thread to query for available scanners.
        
        TODO: clear scanner options until update is finished
        """
        update_thread = UpdateAvailableScannersThread(self.model)
        update_thread.connect("finished", self.on_update_available_scanners_thread_finished)
        self.model.is_scanner_in_use = True
        update_thread.start()
        
    def _clear_scan_modes_sub_menu(self):
        """TODO"""
        for child in self.view['scan_mode_sub_menu'].get_children():
            self.view['scan_mode_sub_menu'].remove(child)
    
    def _clear_scan_resolutions_sub_menu(self):
        """TODO"""
        for child in self.view['scan_resolution_sub_menu'].get_children():
            self.view['scan_resolution_sub_menu'].remove(child)
    
    def _update_scanner_options(self):
        """TODO"""
        self._clear_scan_modes_sub_menu()
            
        self.model.active_scan_mode = None
        menu_item = gtk.MenuItem("Updating scan modes...")
        menu_item.set_sensitive(False)
        self.view['scan_mode_sub_menu'].append(menu_item)
        self.view['scan_mode_sub_menu'].show_all()
        
        self._clear_scan_resolutions_sub_menu()
            
        self.model.active_scan_resolutions = None
        menu_item = gtk.MenuItem("Updating scan resolutions...")
        menu_item.set_sensitive(False)
        self.view['scan_resolution_sub_menu'].append(menu_item)
        self.view['scan_resolution_sub_menu'].show_all()        
            
        update_thread = UpdateScannerOptionsThread(self.model)
        update_thread.connect("finished", self.on_update_scanner_options_thread_finished)
        update_thread.start()