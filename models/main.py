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
This module holds the MainModel, which manages general application
data. 
"""

import logging
import sys

from gtkmvc.model import Model

from nostaples import constants
import nostaples.utils.properties
import saneme

class MainModel(Model):
    """
    Handles data all data not specifically handled by another Model 
    (e.g. the state of the main application window).
    
    Note: active_scanner is a tuple in the format (display_name,
    sane_name).  available_scanners is a list of such tuples.
    """
    __properties__ = \
    {
        'show_toolbar' : True,
        'show_statusbar' : True,
        'show_thumbnails' : True,
        'show_adjustments' : False,
        'rotate_all_pages' : False,
        
        'active_scanner' : None,      # saneme.Device
        'active_mode' : None,
        'active_resolution' : None,
        
        'available_scanners' : [],    # [] of saneme.Device
        'valid_modes' : [],
        'valid_resolutions' : [],
        
        'scan_in_progress' : False,
        'updating_available_scanners' : False,
        'updating_scan_options' : False,
    }

    def __init__(self, application):
        """
        Constructs the MainModel, as well as necessary sub-models.
        """
        self.application = application
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')
        
    def load_state(self):
        """
        Load persisted state from the self.state_manager.
        """
        state_manager = self.application.get_state_manager()
        sane = self.application.get_sane()
        
        self.show_toolbar = state_manager.init_state(
            'show_toolbar', constants.DEFAULT_SHOW_TOOLBAR, 
            nostaples.utils.properties.PropertyStateCallback(self, 'show_toolbar'))
        
        self.show_statusbar = state_manager.init_state(
            'show_statusbar', constants.DEFAULT_SHOW_STATUSBAR, 
            nostaples.utils.properties.PropertyStateCallback(self, 'show_statusbar'))
        
        self.show_thumbnails = state_manager.init_state(
            'show_thumbnails', constants.DEFAULT_SHOW_THUMBNAILS, 
            nostaples.utils.properties.PropertyStateCallback(self, 'show_thumbnails'))
        
        self.show_adjustments = state_manager.init_state(
            'show_adjustments', constants.DEFAULT_SHOW_ADJUSTMENTS, 
            nostaples.utils.properties.PropertyStateCallback(self, 'show_adjustments'))
        
        self.rotate_all_pages = state_manager.init_state(
            'rotate_all_pages', constants.DEFAULT_ROTATE_ALL_PAGES, 
            nostaples.utils.properties.PropertyStateCallback(self, 'rotate_all_pages'))

        # The local representation of active_scanner is a
        # saneme.Device, but it is persisted by its name attribute only.
        try:
            self.active_scanner = sane.get_device_by_name(
                state_manager.init_state(
                'active_scanner', constants.DEFAULT_ACTIVE_SCANNER, 
                self.state_active_scanner_change))
        except saneme.SaneNoSuchDeviceError:
            self.active_scanner = None
        
        self.active_mode = state_manager.init_state(
            'scan_mode', constants.DEFAULT_SCAN_MODE, 
            self.state_scan_mode_change)
        
        self.active_resolution = state_manager.init_state(
            'scan_resolution', constants.DEFAULT_SCAN_RESOLUTION, 
            self.state_scan_resolution_change)
        
    # PROPERTY SETTERS
    
    set_prop_show_toolbar = nostaples.utils.properties.StatefulPropertySetter(
        'show_toolbar')
    set_prop_show_statusbar = nostaples.utils.properties.StatefulPropertySetter(
        'show_statusbar')
    set_prop_show_thumbnails = nostaples.utils.properties.StatefulPropertySetter(
        'show_thumbnails')
    set_prop_show_adjustments = nostaples.utils.properties.StatefulPropertySetter(
        'show_adjustments')
    set_prop_rotate_all_pages = nostaples.utils.properties.StatefulPropertySetter(
        'rotate_all_pages')
        
    def set_prop_active_scanner(self, value):
        """
        Open the new scanner and write its name to the StateManager.
        
        Note: This and all other propertys setters related to scanner hardware
        will force notifications to all observers by setting the old_value
        parameter to None when calling notify_property_value_change().  This
        has the effect of making changes in the active scanner or its available
        options propagate down to the active mode and other dependent
        properties.  This way the GUI and the settings applied to the SANE
        device are kept synchronized.
        """
        main_controller = self.application.get_main_controller()
        
        # Ignore spurious updates
        old_value = self._prop_active_scanner
        
        # Close the old scanner
        if isinstance(old_value, saneme.Device):
            old_value.close()
        
        # Verify that the proper type is being set
        if value is not None:
            assert isinstance(value, saneme.Device)
        
        # Update the internal property variable
        self._prop_active_scanner = value
        
        # Only persist the state if the new value is not None
        # and it can be opened without error.
        # This prevents problems with trying to store a Null
        # value in the state backend and also allows for smooth
        # transitions if a scanner is disconnected and reconnected.
        if value is not None:
            try:
                value.open()
                self.valid_modes = value.options['mode'].constraint
                self.valid_resolutions = \
                    [str(i) for i in value.options['resolution'].constraint]
            except saneme.SaneError:
                exc_info = sys.exc_info()
                main_controller.run_device_exception_dialog(exc_info)
            
            self.application.get_state_manager()['active_scanner'] = value.name
            
        # Emit the property change notification to all observers.
        self.notify_property_value_change(
            'active_scanner', old_value, value)
        
    def set_prop_active_mode(self, value):
        """
        Update the scanner options and write state to the StateManager.
        
        See L{set_prop_active_scanner} for detailed comments.
        """
        self._prop_active_mode = value    
            
        if value is not None:
            # This catches the case where the value is being loaded from state
            # but a scanner has not yet been activated.
            if self.active_scanner:
                try:
                    self.active_scanner.options['mode'].value = value
                except saneme.SaneReloadOptionsError:
                    # TODO
                    pass
            
            self.application.get_state_manager()['scan_mode'] = value   
                     
        self.notify_property_value_change(
            'active_mode', None, value)    
        
    def set_prop_active_resolution(self, value):
        """
        Update the scanner options and write state to the StateManager.
        
        See L{set_prop_active_scanner} for detailed comments.
        """
        self._prop_active_resolution = value
        
        if value is not None:
            # This catches the case where the value is being loaded from state
            # but a scanner has not yet been activated.
            if self.active_scanner:
                try:
                    self.active_scanner.options['resolution'].value = int(value)
                except saneme.SaneReloadOptionsError:
                    # TODO
                    pass
                
            self.application.get_state_manager()['scan_resolution'] = value
            
        self.notify_property_value_change(
            'active_resolution', None, value)
        
    def set_prop_available_scanners(self, value):
        """
        Set the list of available scanners and update the active_scanner.
        
        See L{set_prop_active_scanner} for detailed comments.
        """
        main_controller = self.application.get_main_controller()
        
        self._prop_available_scanners = value
        
        # Force notification
        self.notify_property_value_change(
            'available_scanners', None, value)
        
        if len(value) == 0:
            self.active_scanner = None
        else:           
            # Select the first available scanner if the previously 
            # selected scanner is not in the new list
            if self._prop_active_scanner not in value:
                self.active_scanner = value[0]
            # Otherwise maintain current selection
            else:
                self.active_scanner = self.active_scanner
        
    def set_prop_valid_modes(self, value):
        """
        Set the list of valid scan modes, update the active mode and write state
        to the StateManager.
        
        See L{set_prop_available_scanners} for detailed comments.
        """
        self._prop_valid_modes = value
        
        self.notify_property_value_change(
            'valid_modes', None, value)
        
        # Update the active mode
        if len(value) == 0:
            self.active_mode = None
        else:
            if self.active_mode not in value:
                self.active_mode = value[0]
            else:
                self.active_mode = self.active_mode   
        
    def set_prop_valid_resolutions(self, value):
        """
        Set the list of valid scan resolutions, update the active resolution
        and write state to the StateManager.
        
        See L{set_prop_available_scanners} for detailed comments.
        """
        self._prop_valid_resolutions = value
        
        self.notify_property_value_change(
            'valid_resolutions', None, value)
            
        # Update the active resolution
        if len(value) == 0:
            self.active_resolution = None
        else:
            if self.active_resolution not in value:
                self.active_resolution = value[0]
            else:
                self.active_resolution = self.active_resolution
        
    # STATE CALLBACKS
        
    def state_active_scanner_change(self):
        """Read state, validating the input."""
        state_manager = self.application.get_state_manager()
        sane = self.application.get_sane()
        
        if state_manager['active_scanner'] in self.available_scanners:
            self.active_scanner = sane.get_device_by_name(state_manager['active_scanner'])
        else:
            state_manager['active_scanner'] = self.active_scanner.name
        
    def state_scan_mode_change(self):
        """Read state, validating the input."""
        state_manager = self.application.get_state_manager()
        
        if state_manager['scan_mode'] in self.valid_modes:
            self.active_mode = state_manager['scan_mode']
        else:
            state_manager['scan_mode'] = self.active_mode
        
    def state_scan_resolution_change(self):
        """Read state, validating the input."""
        state_manager = self.application.get_state_manager()
        
        if state_manager['scan_resolution'] in self.valid_resolutions:
            self.active_resolution = state_manager['scan_resolution']
        else:
            state_manager['scan_resolution'] = self.active_resolution
