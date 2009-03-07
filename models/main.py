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
import nostaples.sane as saneme
import nostaples.utils.properties

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
        # Device, but it is persisted by its name attribute only.
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
        
        # Store previous device
        old_value = self._prop_active_scanner
        
        # Close the old scanner (if not None)
        if old_value is not None:
            assert isinstance(old_value, saneme.Device)
                
            if old_value.is_open():
                old_value.close()
        
        # Update the internal property variable
        self._prop_active_scanner = value
        
        # Only persist the state if the new value is not None
        # and it's option constraints can be queried without error.
        if value is not None:
            # Verify that the proper type is being set
            assert isinstance(value, saneme.Device)
            
            # Open the new scanner
            try:            
                value.open()
            except saneme.SaneError:
                exc_info = sys.exc_info()
                main_controller.run_device_exception_dialog(exc_info)
                
            # Load the option constraints (valid_modes, etc.) for the new device
            self._load_scanner_option_constraints(value)
            
            # Manually constrain option values
            if self._prop_active_mode not in self._prop_valid_modes:
                self._prop_active_mode = self._prop_valid_modes[0]
                
            if self._prop_active_resolution not in self._prop_valid_resolutions:
                self._prop_active_resolution = self._prop_valid_resolutions[0]
            
            # Manually push option values to new device
            try:
                try:
                    value.options['mode'].value = self._prop_active_mode
                except saneme.SaneReloadOptionsError:
                    pass                
                
                try:
                    value.options['resolution'].value = \
                        int(self._prop_active_resolution)
                except saneme.SaneReloadOptionsError:
                    pass
            except saneme.SaneError:
                exc_info = sys.exc_info()
                main_controller.run_device_exception_dialog(exc_info)
              
            # Emit change notifications for manually updated properties
            
            self.notify_property_value_change(
                'valid_modes', None, self.valid_modes)
            
            self.notify_property_value_change(
                'valid_resolutions', None, self.valid_resolutions)
            
            self.notify_property_value_change(
                'active_mode', None, self.active_mode)
            
            self.notify_property_value_change(
                'active_resolution', None, self.active_resolution)
            
            # Persist the scanner name
            self.application.get_state_manager()['active_scanner'] = value.name
        
        # Emit the property change notifications     
        self.notify_property_value_change(
            'active_scanner', None, value)
        
    def set_prop_active_mode(self, value):
        """
        Update the scanner options and write state to the StateManager.
        
        See L{set_prop_active_scanner} for detailed comments.
        """
        main_controller = self.application.get_main_controller()
            
        # Set new property value
        self._prop_active_mode = value
        
        # Check if a valid scanner has been loaded (not None)
        if isinstance(self.active_scanner, saneme.Device):
            # The device should always be open if a value is being set
            assert self.active_scanner.is_open()
            
            # Store the current scanner value for comparison
            try:
                scanner_value = self.active_scanner.options['mode'].value
            except saneme.SaneError:
                exc_info = sys.exc_info()
                main_controller.run_device_exception_dialog(exc_info)
            
            # Never re-set a value or set None to a device option
            if value is not None and scanner_value != value:
                try:
                    # Set the new option value
                    self.active_scanner.options['mode'].value = value
                except saneme.SaneReloadOptionsError:
                    # Reload any options that may have changed
                    self._load_scanner_option_values()
                    
        # Never persist None to state
        if value is not None:            
            self.application.get_state_manager()['scan_mode'] = value
        
        # Emit change notification
        self.notify_property_value_change(
            'active_mode', None, value)    
        
    def set_prop_active_resolution(self, value):
        """
        Update the scanner options and write state to the StateManager.
        
        See L{set_prop_active_scanner} for detailed comments.
        """        
        main_controller = self.application.get_main_controller()
        
        # Set new property value
        self._prop_active_resolution = value
        
        # Check if a valid scanner has been loaded (not None)
        if isinstance(self.active_scanner, saneme.Device):
            # The device should always be open if a value is being set
            assert self.active_scanner.is_open()
            
            # Store the current scanner value for comparison
            try:
                scanner_value = self.active_scanner.options['resolution'].value
            except saneme.SaneError:
                exc_info = sys.exc_info()
                main_controller.run_device_exception_dialog(exc_info)
            
            # Never re-set a value or set None to a device option
            if value is not None and scanner_value != int(value):
                try:
                    # Set the new option value
                    self.active_scanner.options['resolution'].value = int(value)
                except saneme.SaneReloadOptionsError:
                    # Reload any options that may have changed
                    self._load_scanner_option_values()
                    
        # Never persist None to state
        if value is not None:            
            self.application.get_state_manager()['scan_resolution'] = value
        
        # Emit change notification
        self.notify_property_value_change(
            'active_resolution', None, value)    
        
    def set_prop_available_scanners(self, value):
        """
        Set the list of available scanners and update the active_scanner.
        
        See L{set_prop_active_scanner} for detailed comments.
        """
        main_controller = self.application.get_main_controller()
        
        self._prop_available_scanners = value
        
        self.notify_property_value_change(
            'available_scanners', None, value)
        
        if len(value) == 0:
            self.active_scanner = None
        elif self._prop_active_scanner not in value:
            self.active_scanner = value[0]
        
    def set_prop_valid_modes(self, value):
        """
        Set the list of valid scan modes, update the active mode and write state
        to the StateManager.
        
        See L{set_prop_available_scanners} for detailed comments.
        """
        self._prop_valid_modes = value
        
        self.notify_property_value_change(
            'valid_modes', None, value)
        
        if len(value) == 0:
            self.active_mode = None
        elif self.active_mode not in value:
            self.active_mode = value[0]
        
    def set_prop_valid_resolutions(self, value):
        """
        Set the list of valid scan resolutions, update the active resolution
        and write state to the StateManager.
        
        See L{set_prop_available_scanners} for detailed comments.
        """
        self._prop_valid_resolutions = value
        
        self.notify_property_value_change(
            'valid_resolutions', None, value)
        
        if len(value) == 0:
            self.active_resolution = None
        elif self.active_resolution not in value:
            self.active_resolution = value[0]
        
    # STATE CALLBACKS
        
    def state_active_scanner_change(self):
        """Read state, validating the input."""
        state_manager = self.application.get_state_manager()
        sane = self.application.get_sane()
        
        if state_manager['active_scanner'] in self.available_scanners:
            self.active_scanner = sane.get_device_by_name(
                state_manager['active_scanner'])
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

    # INTERNAL METHODS
            
    def _load_scanner_option_constraints(self, sane_device):
        """
        Load the option constraints from a specified scanner.
        """
        main_controller = self.application.get_main_controller()
        
        try:
            assert sane_device.options['mode'].constraint_type == \
                saneme.OPTION_CONSTRAINT_STRING_LIST
                
            self._prop_valid_modes = sane_device.options['mode'].constraint
            
            if sane_device.options['resolution'].constraint_type == \
                saneme.OPTION_CONSTRAINT_RANGE:
                min, max, step = sane_device.options['resolution'].constraint
                
                resolutions = []
                
                # If there are not an excessive number, include every possible
                # resolution
                if (max - min) / step <= constants.MAX_VALID_OPTION_VALUES:                
                    i = min
                    while i <= max:
                        resolutions.append(str(i))
                        i = i + step
                # Otherwise, take a crack at building a sensible set of options
                # that mean that constraint criteria
                else:
                    i = 1
                    increment = (max - min) / (constants.MAX_VALID_OPTION_VALUES - 1)
                    while (i <= constants.MAX_VALID_OPTION_VALUES - 2):
                        unrounded = min + (i * increment)
                        rounded = int(round(unrounded / step) * step)
                        resolutions.append(str(rounded))
                        i = i + 1
                    resolutions.insert(0, str(min))
                    resolutions.append(str(max))
                    
                self._prop_valid_resolutions = resolutions
            elif sane_device.options['resolution'].constraint_type == \
                saneme.OPTION_CONSTRAINT_INTEGER_LIST:
                self._prop_valid_resolutions = \
                    [str(i) for i in sane_device.options['resolution'].constraint]
            elif sane_device.options['resolution'].constraint_type == \
                saneme.OPTION_CONSTRAINT_STRING_LIST:
                    sane_device.options['resolution'].constraint
            else:
                raise AssertionError('Unsupported constraint type.')              
        except saneme.SaneError:
            exc_info = sys.exc_info()
            main_controller.run_device_exception_dialog(exc_info)
    
    def _load_scanner_option_values(self):
        """
        Get current scanner options from the active_scanner.
        
        Useful for reloading any option that may have changed in response to
        a SaneReloadOptionsError.
        """
        main_controller = self.application.get_main_controller()
        
        try:
            # TODO: ReloadOptions should reload constraints as well as values!
            self.active_mode = self.active_scanner.options['mode'].value
            self.active_resolution = \
                str(self.active_scanner.options['resolution'].value)
        except saneme.SaneError:
            exc_info = sys.exc_info()
            main_controller.run_device_exception_dialog(exc_info)