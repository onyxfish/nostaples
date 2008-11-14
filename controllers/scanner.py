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
This module holds the L{PageController}, which manages interaction 
between the L{PageModel} and L{PageView}.
"""

import commands
import logging
import os
import re
import tempfile

import gobject
import gtk
from gtkmvc.controller import Controller
import threading

import constants

class ScanningThread(gobject.GObject, threading.Thread):
    """
    A specialized thread that scans a page and emits status
    callbacks on the main thread.
    
    This class is based on an example by John Stowers:
    U{http://www.johnstowers.co.nz/blog/index.php/tag/pygtk/}
    """
    __gsignals__ =  {
            "succeeded": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
            "failed": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
            }
    
    def __init__(self, scanning_model):
        """
        Initialize the thread and get a tempfile name that
        will house the scanned image.
        """
        gobject.GObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.model = scanning_model
        self.path = tempfile.mktemp()
        
        self.log.debug('Created targetting temp file %s.' % self.path)
        
    def emit(self, *args):
        """
        Override the emit method so that callbacks always occur on the
        main GTK thread.
        """
        gobject.idle_add(gobject.GObject.emit,self,*args)
    
    def run(self):
        """
        Scan a page and emit status callbacks.
        """
        scan_program = 'scanimage --format=pnm'
        mode_flag = ' '.join(['--mode', self.model.active_mode])
        resolution_flag = ' '.join(['--resolution', self.model.active_resolution])
        scanner_flag = ' '.join(['-d', self.model.sane_name])
        output_file = '>%s' % self.path
        scan_command = ' '.join(
            [scan_program, mode_flag, resolution_flag, scanner_flag, output_file])
        
        self.log.info(
            'Scanning with command: "%s".' % scan_command)
        output = commands.getoutput(scan_command)
        
        # TODO: check output for errors?
        
        if not os.path.exists(self.path):
            self.log.error(
                'Failed: temp file %s not created.' % self.path)
            self.emit("failed")
        
        if os.stat(self.path).st_size <= 0:
            self.log.error(
                'Failed: temp file %s is empty.' % self.path)
            os.remove(path)
            self.emit("failed")

        self.emit("succeeded", self.path)

class ScannerController(Controller):
    """
    Manages interaction between the L{ScannerModel} and L{ScannerView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, model):
        """
        Constructs the Scannerontroller.
        """
        Controller.__init__(self, model)

        self.log = logging.getLogger(self.__class__.__name__)
        
        self.is_in_use = False
        
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
    
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
    
    # PROPERTY CALLBACKS
    
    def property_valid_modes_value_change(self, model, old_value, new_value):
        """
        Updates the list of valid scan modes for the current scanner.
        """        
        # Clear scan modes sub menu
        for child in self.view['scan_mode_sub_menu'].get_children():
            self.view['scan_mode_sub_menu'].remove(child)
        
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
        # Clear scan modes sub menu
        for child in self.view['scan_resolution_sub_menu'].get_children():
            self.view['scan_resolution_sub_menu'].remove(child)
        
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
    
    # MISCELLANEOUS CALLBACKS
    
    def on_scan_finished(self, scan_thread, *args):
        """Mark that the scanner is no longer in use."""
        self.is_in_use = False
    
    # PUBLIC METHODS
    
    def set_model(self, scanner_model):
        """
        Sets the PageModel that is currently being displayed in the preview area.
        """
        self.model.unregister_observer(self)
        self.model = scanner_model
        self.model.register_observer(self)
        
        self._update_scanner_options()
        
    def scan_to_file(self, on_scan_succeeded, on_scan_failed):
        """
        Creates a L{ScanningThread} and executes it, connecting
        callbacks to report on the scan status.
        """
        if self.is_in_use:
            # TODO: notify user that the scanner is in use
            return
        
        scanning_thread = ScanningThread(self.model)
        scanning_thread.connect("succeeded", on_scan_succeeded)
        scanning_thread.connect("succeeded", self.on_scan_finished)
        scanning_thread.connect("failed", on_scan_failed)
        scanning_thread.connect("failed", self.on_scan_finished)
        scanning_thread.start()
        
        self.is_in_use = True
    
    # PRIVATE (INTERNAL) METHODS
    
    def _update_scanner_options(self):
        """
        Queries SANE for a list of available options for the specified scanner.    
        """        
        update_command = ' '.join(['scanimage --help -d',  self.model.sane_name])
        self.log.debug(
            'Updating scanner options with command: "%s".' % \
            update_command)
        output = commands.getoutput(update_command)
        
        # TODO: check that scanner was found

        try:
            mode_list = re.findall('--mode (.*) ', output)[0].split('|')
        except IndexError:
            self.log.warn(
                'Could not parse scan modes or no modes available for \
                device "%s".' % self.model.display_name)
            mode_list = []
            
        try:
            resolution_list = re.findall('--resolution (.*)dpi ', output)[0].split('|')
        except IndexError:
            self.log.warn(
                'Could not parse resolutions or no resolutions available for \
                device "%s".' % self.model.display_name)
            resolution_list = []
        
        self.model.valid_modes = mode_list
        self.model.valid_resolutions = resolution_list