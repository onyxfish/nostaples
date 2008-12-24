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

from models.page import PageModel
from utils.scanning import *

class MainController(Controller):
    """
    Manages interaction between the L{MainModel} and L{MainView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the MainController, as well as necessary sub-controllers 
        and services.
        """
        self.application = application
        Controller.__init__(self, application.get_main_model())

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')        
        
        application.get_document_model().register_observer(self)

    def register_view(self, view):
        """
        Registers this controller with a view.
        
        Also, invokes the L{MainModel.load_state} which will
        pull in any persisted values and then calls
        L{_update_available_scanners} to poll for devices and
        create relevant widgets in the view.
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
        self.application.show_save_dialog()
    
    def on_delete_menu_item_activate(self, menu_item):
        self.application.get_document_controller().delete_selected()
    
    def on_insert_scan_menu_item_activate(self, menu_item):
        """Scan a page into the current document."""
        self._scan()
    
    def on_preferences_menu_item_activate(self, menu_item):
        """Creates and displays a preferences dialog."""
        self.application.show_preferences_dialog()
        
    def on_quit_menu_item_activate(self, menu_item):
        """Exits the application."""
        self.quit()
            
    def on_zoom_in_menu_item_activate(self, menu_item):
        """Zooms the page preview in."""
        self.application.get_page_controller().zoom_in()
    
    def on_zoom_out_menu_item_activate(self, menu_item):
        """Zooms the page preview out."""
        self.application.get_page_controller().zoom_out()
    
    def on_zoom_one_to_one_menu_item_activate(self, menu_item):
        """Zooms the page preview to the true size of the scanned image."""
        self.application.get_page_controller().zoom_one_to_one()
        
    def on_zoom_best_fit_menu_item_activate(self, menu_item):
        """Zooms the page preview to best fit within the preview window."""
        self.application.get_page_controller().zoom_best_fit()
        
    def on_rotate_clockwise_menu_item_activate(self, menu_item):
        """Rotates the visible page ninety degress clockwise."""
        self.application.get_page_controller().rotate_clockwise()
        
    def on_rotate_counter_clockwise_menu_item_activate(self, menu_item):
        """Rotates the visible page ninety degress counter-clockwise."""
        self.application.get_page_controller().rotate_counter_clockwise()
        
    def on_rotate_all_pages_menu_item_toggled(self, menu_item):
        """TODO"""
        pass
        
    def on_available_scanner_menu_item_toggled(self, menu_item):
        """
        Set the active scanner.
        
        TODO: Need a second scanner to properly test this...
        """
        main_model = self.application.get_main_model()
        
        if menu_item.get_active():
            for scanner in main_model.available_scanners:
                if scanner[0] == menu_item.get_children()[0].get_text():
                    main_model.active_scanner = scanner
                    return
                
    def on_refresh_available_scanners_menu_item_activate(self, menu_item):
        """Refresh the list of connected scanners from SANE."""
        self._update_available_scanners()
        
    def on_valid_mode_menu_item_toggled(self, menu_item):
        """Sets the active scan mode."""
        if menu_item.get_active():
            self.application.get_main_model().active_mode = \
                menu_item.get_children()[0].get_text()

    def on_valid_resolution_menu_item_toggled(self, menu_item):
        """Sets the active scan resolution."""
        if menu_item.get_active():
            self.application.get_main_model().active_resolution = \
                menu_item.get_children()[0].get_text() 
                
    def on_go_first_menu_item_activate(self, menu_item):
        """Selects the first scanned page."""
        self.application.get_document_controller().goto_first_page()
        
    def on_go_previous_menu_item_activate(self, menu_item):
        """Selects the scanned page before to the currently selected one."""
        self.application.get_document_controller().goto_previous_page()
    
    def on_go_next_menu_item_activate(self, menu_item):
        """Selects the scanned page after to the currently selected one."""
        self.application.get_document_controller().goto_next_page()
    
    def on_go_last_menu_item_activate(self, menu_item):
        """Selects the last scanned page."""
        self.application.get_document_controller().goto_last_page()
        
    def on_contents_menu_item_clicked(self, menu_item):
        """TODO"""
        pass
    
    def on_about_menu_item_activate(self, menu_item):
        """Show the about dialog."""
        self.application.show_about_dialog()
        
    # Toolbar Buttons
        
    def on_scan_button_clicked(self, button):
        """Scan a page into the current document."""
        self._scan()
        
    def on_save_as_button_clicked(self, button):
        """Saves the current document to a file."""
        self.application.show_save_dialog()
    
    def on_zoom_in_button_clicked(self, button):
        """Zooms the page preview in."""
        self.application.get_page_controller().zoom_in()
    
    def on_zoom_out_button_clicked(self, button):
        """Zooms the page preview out."""
        self.application.get_page_controller().zoom_out()
    
    def on_zoom_one_to_one_button_clicked(self, button):
        """Zooms the page preview to the true size of the scanned image."""
        self.application.get_page_controller().zoom_one_to_one()
    
    def on_zoom_best_fit_button_clicked(self, button):
        """Zooms the page preview to best fit within the preview window."""
        self.application.get_page_controller().zoom_best_fit()
        
    def on_rotate_clockwise_button_clicked(self, button):
        """Rotates the visible page ninety degress clockwise."""
        self.application.get_page_controller().rotate_clockwise()
        
    def on_rotate_counter_clockwise_button_clicked(self, button):
        """Rotates the visible page ninety degress counter-clockwise."""
        self.application.get_page_controller().rotate_counter_clockwise()
        
    def on_go_first_button_clicked(self, button):
        """Selects the first scanned page."""
        self.application.get_document_controller().goto_first_page()
        
    def on_go_previous_button_clicked(self, button):
        """Selects the scanned page before to the currently selected one."""
        self.application.get_document_controller().goto_previous_page()
    
    def on_go_next_button_clicked(self, button):
        """Selects the scanned page after to the currently selected one."""
        self.application.get_document_controller().goto_next_page()
    
    def on_go_last_button_clicked(self, button):
        """Selects the last scanned page."""
        self.application.get_document_controller().goto_last_page()
    
    # MainModel PROPERTY CALLBACKS
    
    def property_show_toolbar_value_change(self, model, old_value, new_value):
        """Update the visibility of the toolbar."""
        main_view = self.application.get_main_view()
        
        menu_item = main_view['show_toolbar_menu_item']
        menu_item.set_active(new_value)
        
        if new_value:
            main_view['main_toolbar'].show()
        else:
            main_view['main_toolbar'].hide()
    
    def property_show_statusbar_value_change(self, model, old_value, new_value):
        """Update the visibility of the statusbar."""
        main_view = self.application.get_main_view()
        
        menu_item = main_view['show_statusbar_menu_item']
        menu_item.set_active(new_value)
        
        if new_value:
            main_view['scan_window_statusbar'].show()
        else:
            main_view['scan_window_statusbar'].hide()

    def property_show_thumbnails_value_change(self, model, old_value, new_value):
        """Update the visibility of the thumbnails."""
        main_view = self.application.get_main_view()
        menu_item = main_view['show_thumbnails_menu_item']
        menu_item.set_active(new_value)
        
        self.application.get_document_controller().toggle_thumbnails_visible(new_value)

    def property_show_adjustments_value_change(self, model, old_value, new_value):
        """Update the visibility of the adjustments controls."""
        main_view = self.application.get_main_view()
        menu_item = main_view['show_adjustments_menu_item']
        menu_item.set_active(new_value)
        
        self.application.get_document_controller().toggle_adjustments_visible(new_value)    
        
    def property_active_scanner_value_change(self, model, old_value, new_value):
        """
        Update the menu and valid scanner options to match the new device.
        """
        main_view = self.application.get_main_view()
        
        for menu_item in main_view['scanner_sub_menu'].get_children():
            if menu_item.get_children()[0].get_text() == new_value[0]:
                menu_item.set_active(True)
                break
        
        self._update_scanner_options()
        
    def property_active_mode_value_change(self, model, old_value, new_value):
        """Select the active mode from in the menu."""
        main_view = self.application.get_main_view()
        
        for menu_item in main_view['scan_mode_sub_menu'].get_children():
            if menu_item.get_children()[0].get_text() == new_value:
                menu_item.set_active(True)
                break
    
    def property_active_resolution_value_change(self, model, old_value, new_value):
        """Select the active resolution from in the menu."""
        main_view = self.application.get_main_view()
        
        for menu_item in main_view['scan_resolution_sub_menu'].get_children():
            if menu_item.get_children()[0].get_text() == new_value:
                menu_item.set_active(True)
                break
            
    def property_available_scanners_value_change(self, model, old_value, new_value):
        """
        Update the menu of available scanners.
        """
        main_view = self.application.get_main_view()
        
        self._clear_available_scanners_sub_menu()
        
        # Generate the new menu
        if len(new_value) == 0:
            menu_item = gtk.MenuItem('No Scanners Connected')
            menu_item.set_sensitive(False)
            main_view['scanner_sub_menu'].append(menu_item)
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
                
                main_view['scanner_sub_menu'].append(menu_item)
        
        menu_item = gtk.MenuItem('Refresh List')
        menu_item.connect('activate', self.on_refresh_available_scanners_menu_item_activate)
        main_view['scanner_sub_menu'].append(menu_item)
        
        main_view['scanner_sub_menu'].show_all()
        
    def property_valid_modes_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan modes for the current scanner.
        """
        main_view = self.application.get_main_view()
        
        self._clear_scan_modes_sub_menu()
        
        if len(new_value) == 0:
            menu_item = gtk.MenuItem("No Scan Modes")
            menu_item.set_sensitive(False)
            main_view['scan_mode_sub_menu'].append(menu_item)
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
                main_view['scan_mode_sub_menu'].append(menu_item)
            
        main_view['scan_mode_sub_menu'].show_all()
    
    def property_valid_resolutions_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan resolutions for the current scanner.
        """
        main_view = self.application.get_main_view()
        
        self._clear_scan_resolutions_sub_menu()
        
        if len(new_value) == 0:
            menu_item = gtk.MenuItem("No Scan Resolutions")
            menu_item.set_sensitive(False)
            main_view['scan_resolution_sub_menu'].append(menu_item)
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
                main_view['scan_resolution_sub_menu'].append(menu_item)
            
        main_view['scan_resolution_sub_menu'].show_all()
        
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
        
    # DocumentModel PROPERTY CALLBACKS
    
    def property_count_value_change(self, model, old_value, new_value):
        """Toggle available controls."""
        self._toggle_document_controls()
    
    # THREAD CALLBACKS
    
    def on_scan_succeeded(self, scanning_thread, filename):
        """Append the new page to the current document."""
        main_model = self.application.get_main_model()
        
        new_page = PageModel(filename, int(main_model.active_resolution))
        self.application.get_document_model().append(new_page)
        main_model.scan_in_progress = False
    
    def on_scan_failed(self, scanning_thread):
        """
        Set that scan is complete.
        
        TODO: check if the scanner has been disconnected
        """
        self.application.get_main_model().scan_in_progress = False
        
    def on_update_available_scanners_thread_finished(self, update_thread, scanner_list):
        """Set the new list of available scanners."""
        self.application.get_main_model().available_scanners = scanner_list
        self.application.get_main_model().updating_available_scanners = False
            
    def on_update_scanner_options_thread_finished(self, update_thread, mode_list, resolution_list):
        """
        Update the mode and resolution lists and rark that
        the scanner is no longer in use.
        """
        main_model = self.application.get_main_model()
        main_model.valid_modes = mode_list
        main_model.valid_resolutions = resolution_list
        main_model.updating_scan_options = False
        
    # PUBLIC METHODS
        
    def quit(self):
        """Exits the application."""
        self.log.debug('Quit.')
        gtk.main_quit()

    # PRIVATE METHODS
        
    def _clear_available_scanners_sub_menu(self):
        """Clear the menu of available scanners."""
        main_view = self.application.get_main_view()
        
        for child in main_view['scanner_sub_menu'].get_children():
            main_view['scanner_sub_menu'].remove(child)
        
    def _clear_scan_modes_sub_menu(self):
        """Clear the menu of valid scan modes."""
        main_view = self.application.get_main_view()
        
        for child in main_view['scan_mode_sub_menu'].get_children():
            main_view['scan_mode_sub_menu'].remove(child)
    
    def _clear_scan_resolutions_sub_menu(self):
        """Clear the menu of valid scan resolutions."""
        main_view = self.application.get_main_view()
        
        for child in main_view['scan_resolution_sub_menu'].get_children():
            main_view['scan_resolution_sub_menu'].remove(child)
            
    def _toggle_scan_controls(self):
        """Toggle whether or not the scan controls or accessible."""
        main_model = self.application.get_main_model()
        main_view = self.application.get_main_view()
        
        if main_model.scan_in_progress or main_model.updating_available_scanners or \
            main_model.updating_scan_options:
            main_view.set_scan_controls_sensitive(False)
        else:
            main_view.set_scan_controls_sensitive(True)
            
    def _toggle_document_controls(self):
        """
        Toggle available document controls based on the current scanner
        status and the number of scanned pages.
        """
        main_model = self.application.get_main_model()
        main_view = self.application.get_main_view()
        
        # Disable all controls when the scanner is in use
        if main_model.scan_in_progress or main_model.updating_available_scanners or \
            main_model.updating_scan_options:
            main_view.set_file_controls_sensitive(False)
            main_view.set_delete_controls_sensitive(False)
            main_view.set_zoom_controls_sensitive(False)
            main_view.set_adjustment_controls_sensitive(False)        
            main_view.set_navigation_controls_sensitive(False)
        else:
            count = self.application.get_document_model().count
            
            # Disable all controls if no pages are scanned
            if count == 0:
                main_view.set_file_controls_sensitive(False)
                main_view.set_delete_controls_sensitive(False)
                main_view.set_zoom_controls_sensitive(False)
                main_view.set_adjustment_controls_sensitive(False)        
                main_view.set_navigation_controls_sensitive(False)
            else:
                # Enable most controls if any pages scanned
                main_view.set_file_controls_sensitive(True)
                main_view.set_delete_controls_sensitive(True)
                main_view.set_zoom_controls_sensitive(True)
                main_view.set_adjustment_controls_sensitive(True)  
                
                # Only enable navigation if more than one page scanned
                if count > 1:      
                    main_view.set_navigation_controls_sensitive(True)
                else:
                    main_view.set_navigation_controls_sensitive(False)                    
    
    def _scan(self):
        """Begin a scan."""
        main_model = self.application.get_main_model()
        
        main_model.scan_in_progress = True
        scanning_thread = ScanningThread(main_model)
        scanning_thread.connect("succeeded", self.on_scan_succeeded)
        scanning_thread.connect("failed", self.on_scan_failed)
        scanning_thread.start()
            
    def _update_available_scanners(self):
        """
        Start a new update thread to query for available scanners.
        """        
        main_model = self.application.get_main_model()
        
        main_model.updating_available_scanners = True
        update_thread = UpdateAvailableScannersThread(main_model)
        update_thread.connect("finished", self.on_update_available_scanners_thread_finished)
        update_thread.start()
    
    def _update_scanner_options(self):
        """Determine the valid options for the current scanner."""  
        main_model = self.application.get_main_model()
                  
        main_model.updating_scan_options = True
        update_thread = UpdateScannerOptionsThread(main_model)
        update_thread.connect("finished", self.on_update_scanner_options_thread_finished)
        update_thread.start()