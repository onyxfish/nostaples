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
        self.model.document_model.register_observer(self)

    def register_view(self, view):
        """
        Registers this controller with a view.
        
        Also, invokes the L{MainModel.load_state} which will
        pull in any persisted values and then calls
        L{_update_available_scanners} to poll for devices and
        create relevant widgets in the view.
        """
        Controller.register_view(self, view)
        
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
    
    # Menu Items
        
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
        """
        Set the active scanner.
        
        TODO: Need a second scanner to properly test this...
        """
        if menu_item.get_active():
            for scanner in self.model.available_scanners:
                if scanner[0] == menu_item.get_children()[0].get_text():
                    self.model.active_scanner = scanner
                    return
                
    def on_refresh_available_scanners_menu_item_activate(self, menu_item):
        """Refresh the list of connected scanners from SANE."""
        self._update_available_scanners()
        
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
        
    def on_contents_menu_item_clicked(self, menu_item):
        """TODO"""
        pass
    
    def on_about_menu_item_activate(self, menu_item):
        """TODO"""
        pass
        
    # Toolbar Buttons
        
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
        
    def property_active_scanner_value_change(self, model, old_value, new_value):
        """
        Update the menu and valid scanner options to match the new device.
        """
        for menu_item in self.view['scanner_sub_menu'].get_children():
            if menu_item.get_children()[0].get_text() == new_value[0]:
                menu_item.set_active(True)
                break
        
        self._update_scanner_options()
        
    def property_active_mode_value_change(self, model, old_value, new_value):
        """Select the active mode from in the menu."""
        for menu_item in self.view['scan_mode_sub_menu'].get_children():
            if menu_item.get_children()[0].get_text() == new_value:
                menu_item.set_active(True)
                break
    
    def property_active_resolution_value_change(self, model, old_value, new_value):
        """Select the active resolution from in the menu."""
        for menu_item in self.view['scan_resolution_sub_menu'].get_children():
            if menu_item.get_children()[0].get_text() == new_value:
                menu_item.set_active(True)
                break
            
    def property_available_scanners_value_change(self, model, old_value, new_value):
        """
        Update the menu of available scanners.
        """
        self._clear_available_scanners_sub_menu()
        
        # Generate the new menu
        if len(new_value) == 0:
            menu_item = gtk.MenuItem('No Scanners Connected')
            menu_item.set_sensitive(False)
            self.view['scanner_sub_menu'].append(menu_item)
        else:
            first_item = None

            for i in range(len(new_value)):
                # The first menu item defines the group
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, new_value[i][0])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, new_value[i][0])
                
                self.view['scanner_sub_menu'].append(menu_item)
        
        menu_item = gtk.MenuItem('Refresh List')
        menu_item.connect('activate', self.on_refresh_available_scanners_menu_item_activate)
        self.view['scanner_sub_menu'].append(menu_item)
        
        self.view['scanner_sub_menu'].show_all()
        
    def property_valid_modes_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan modes for the current scanner.
        """
        self._clear_scan_modes_sub_menu()
        
        if len(new_value) == 0:
            menu_item = gtk.MenuItem("No Scan Modes")
            menu_item.set_sensitive(False)
            self.view['scan_mode_sub_menu'].append(menu_item)
        else:        
            for i in range(len(new_value)):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, new_value[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, new_value[i])
                
                menu_item.connect('toggled', self.on_valid_mode_menu_item_toggled)
                self.view['scan_mode_sub_menu'].append(menu_item)
            
        self.view['scan_mode_sub_menu'].show_all()
    
    def property_valid_resolutions_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan resolutions for the current scanner.
        """
        self._clear_scan_resolutions_sub_menu()
        
        if len(new_value) == 0:
            menu_item = gtk.MenuItem("No Scan Resolutions")
            menu_item.set_sensitive(False)
            self.view['scan_resolution_sub_menu'].append(menu_item)
        else:        
            for i in range(len(new_value)):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(
                        None, new_value[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(
                        first_item, new_value[i])
                
                menu_item.connect('toggled', self.on_valid_resolution_menu_item_toggled)
                self.view['scan_resolution_sub_menu'].append(menu_item)
            
        self.view['scan_resolution_sub_menu'].show_all()
        
    def property_scan_in_progress_value_change(self, model, old_value, new_value):
        """Disable or re-enable scan controls."""
        self._toggle_scan_controls()
        self._toggle_document_controls()
        
    def property_updating_available_scanners_value_change(self, model, old_value, new_value):
        """Disable or re-enable scan controls."""
        self._toggle_scan_controls()
        self._toggle_document_controls()
    
    def property_updating_scan_options_value_change(self, model, old_value, new_value):
        """Disable or re-enable scan controls."""
        self._toggle_scan_controls()
        self._toggle_document_controls()
        
    def property_is_document_empty_value_change(self, model, old_value, new_value):
        """
        Disable file and page manipulation controls if no pages have been scanned.
        """
        self._toggle_document_controls()
        
    def property_is_document_multiple_pages_value_change(self, model, old_value, new_value):
        """
        Disable navigation controls if only one page has been scanned.
        """
        self._toggle_document_controls()
    
    # THREAD CALLBACKS
    
    def on_scan_succeeded(self, scanning_thread, filename):
        """Append the new page to the current document."""
        new_page = PageModel(filename, int(self.model.active_resolution))
        self.model.document_model.append(new_page)
        self.model.scan_in_progress = False
    
    def on_scan_failed(self, scanning_thread):
        """
        Set that scan is complete.
        
        TODO: check if the scanner has been disconnected
        """
        self.model.scan_in_progress = False
        
    def on_update_available_scanners_thread_finished(self, update_thread, scanner_list):
        """Set the new list of available scanners."""
        self.model.available_scanners = scanner_list
        self.model.updating_available_scanners = False
            
    def on_update_scanner_options_thread_finished(self, update_thread, mode_list, resolution_list):
        """
        Update the mode and resolution lists and rark that
        the scanner is no longer in use.
        """
        self.model.valid_modes = mode_list
        self.model.valid_resolutions = resolution_list
        self.model.updating_scan_options = False
        
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
        
    def _clear_available_scanners_sub_menu(self):
        """Clear the menu of available scanners."""
        for child in self.view['scanner_sub_menu'].get_children():
            self.view['scanner_sub_menu'].remove(child)
        
    def _clear_scan_modes_sub_menu(self):
        """Clear the menu of valid scan modes."""
        for child in self.view['scan_mode_sub_menu'].get_children():
            self.view['scan_mode_sub_menu'].remove(child)
    
    def _clear_scan_resolutions_sub_menu(self):
        """Clear the menu of valid scan resolutions."""
        for child in self.view['scan_resolution_sub_menu'].get_children():
            self.view['scan_resolution_sub_menu'].remove(child)
            
    def _toggle_scan_controls(self):
        """Toggle whether or not the scan controls or accessible."""
        if self.model.scan_in_progress or self.model.updating_available_scanners or \
            self.model.updating_scan_options:
            self.view.set_scan_controls_sensitive(False)
        else:
            self.view.set_scan_controls_sensitive(True)
            
    def _toggle_document_controls(self):
        """TODO"""
        print self.model.is_document_multiple_pages
        # Disable all controls when the scanner is in use
        if self.model.scan_in_progress or self.model.updating_available_scanners or \
            self.model.updating_scan_options:
            self.view.set_file_controls_sensitive(False)
            self.view.set_delete_controls_sensitive(False)
            self.view.set_zoom_controls_sensitive(False)
            self.view.set_adjustment_controls_sensitive(False)        
            self.view.set_navigation_controls_sensitive(False)
        else:
            # Disable all controls if no pages are scanned
            if self.model.is_document_empty:
                self.view.set_file_controls_sensitive(False)
                self.view.set_delete_controls_sensitive(False)
                self.view.set_zoom_controls_sensitive(False)
                self.view.set_adjustment_controls_sensitive(False)        
                self.view.set_navigation_controls_sensitive(False)
            else:
                # Enable most controls if any pages scanned
                self.view.set_file_controls_sensitive(True)
                self.view.set_delete_controls_sensitive(True)
                self.view.set_zoom_controls_sensitive(True)
                self.view.set_adjustment_controls_sensitive(True)  
                
                # Only enable navigation if more than one page scanned
                if self.model.is_document_multiple_pages:      
                    self.view.set_navigation_controls_sensitive(True)
                else:
                    self.view.set_navigation_controls_sensitive(False)                    
    
    def _scan(self):
        """Begin a scan."""
        self.model.scan_in_progress = True
        scanning_thread = ScanningThread(self.model)
        scanning_thread.connect("succeeded", self.on_scan_succeeded)
        scanning_thread.connect("failed", self.on_scan_failed)
        scanning_thread.start()
            
    def _update_available_scanners(self):
        """
        Start a new update thread to query for available scanners.
        """        
        self.model.updating_available_scanners = True
        update_thread = UpdateAvailableScannersThread(self.model)
        update_thread.connect("finished", self.on_update_available_scanners_thread_finished)
        update_thread.start()
    
    def _update_scanner_options(self):
        """Determine the valid options for the current scanner."""            
        self.model.updating_scan_options = True
        update_thread = UpdateScannerOptionsThread(self.model)
        update_thread.connect("finished", self.on_update_scanner_options_thread_finished)
        update_thread.start()