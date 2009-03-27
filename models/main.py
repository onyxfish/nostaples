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
from reportlab.lib.pagesizes import inch as points_per_inch
from reportlab.lib.pagesizes import cm as points_per_cm

from nostaples import constants
import nostaples.sane as saneme
from nostaples.utils import properties

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
        'active_page_size' : None,
        
        'available_scanners' : [],    # [] of saneme.Device
        'unavailable_scanners' : [],  # [] of (saneme.Device.display_name, reason) tuples
        'valid_modes' : [],
        'valid_resolutions' : [],
        'valid_page_sizes' : [],
        
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
            properties.PropertyStateCallback(self, 'show_toolbar'))
        
        self.show_statusbar = state_manager.init_state(
            'show_statusbar', constants.DEFAULT_SHOW_STATUSBAR, 
            properties.PropertyStateCallback(self, 'show_statusbar'))
        
        self.show_thumbnails = state_manager.init_state(
            'show_thumbnails', constants.DEFAULT_SHOW_THUMBNAILS, 
            properties.PropertyStateCallback(self, 'show_thumbnails'))
        
        self.show_adjustments = state_manager.init_state(
            'show_adjustments', constants.DEFAULT_SHOW_ADJUSTMENTS, 
            properties.PropertyStateCallback(self, 'show_adjustments'))
        
        self.rotate_all_pages = state_manager.init_state(
            'rotate_all_pages', constants.DEFAULT_ROTATE_ALL_PAGES, 
            properties.PropertyStateCallback(self, 'rotate_all_pages'))

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
        
#        self.active_page_size = state_manager.init_state(
#            'page_size', constants.DEFAULT_PAGE_SIZE, 
#            self.state_page_size_change)
        
    # PROPERTY SETTERS
    
    set_prop_show_toolbar = properties.StatefulPropertySetter(
        'show_toolbar')
    set_prop_show_statusbar = properties.StatefulPropertySetter(
        'show_statusbar')
    set_prop_show_thumbnails = properties.StatefulPropertySetter(
        'show_thumbnails')
    set_prop_show_adjustments = properties.StatefulPropertySetter(
        'show_adjustments')
    set_prop_rotate_all_pages = properties.StatefulPropertySetter(
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
                self.log.debug(
                    'Setting active scanner to %s.' % value.display_name)         
                value.open()
            except saneme.SaneError:
                exc_info = sys.exc_info()
                main_controller.run_device_exception_dialog(exc_info)

            # Get valid options from the new device and then reset the
            # previous options if they exist on the new device
            self._update_valid_modes()
            self.active_mode = self.active_mode
            self._update_valid_resolutions()
            self.active_resolution = self.active_resolution
            self._update_valid_page_sizes()
            self.active_page_size = self.active_page_size
            
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
                    self.log.debug(
                        'Setting active mode to %s.' % value)
                    self.active_scanner.options['mode'].value = value
                except saneme.SaneInexactValueError:
                    # TODO - what if "exact" value isn't in the list?
                    pass
                except saneme.SaneReloadOptionsError:
                    # Reload any options that may have changed, this will
                    # also force this value to be set again, so its safe to 
                    # return immediately
                    self._reload_scanner_options()
                    return
                    
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
                    self.log.debug(
                        'Setting active resolution to %s.' % value)  
                    self.active_scanner.options['resolution'].value = int(value)
                except saneme.SaneInexactValueError:
                    # TODO - what if "exact" value isn't in the list?
                    pass
                except saneme.SaneReloadOptionsError:
                    # Reload any options that may have changed, this will
                    # also force this value to be set again, so its safe to 
                    # return immediately
                    self._reload_scanner_options()
                    return
                    
        # Never persist None to state
        if value is not None:            
            self.application.get_state_manager()['scan_resolution'] = value
        
        # Emit change notification
        self.notify_property_value_change(
            'active_resolution', None, value)    
        
    def set_prop_active_page_size(self, value):
        # TODO
        pass
        
    def set_prop_available_scanners(self, value):
        """
        Takes a new list of scanners, removes any which are blacklisted or
        unsupported, sets the new list, updates the active_scanner, and emits
        appropriate property callbacks.
        
        See L{set_prop_active_scanner} for detailed comments.
        """
        main_controller = self.application.get_main_controller()
        preferences_model = self.application.get_preferences_model()
        
        # Remove blacklisted scanners
        value = \
            [scanner for scanner in value if not \
             scanner.display_name in preferences_model.blacklisted_scanners]
        
        # Remove scanners that do not support necessary options or fail to
        # open entirely
        new_unavailable_scanners = []
        
        # TODO - move somewhere more appropriate?
        unsupported_scanner_error = \
            'Scanner %s is unsupported for the following reason: %s'
                        
        for scanner in value:
            try:
                scanner.open()
                
                unsupported = False
                
                # Enforce mode option requirements
                if not scanner.has_option('mode'):
                    reason = 'No \'mode\' option.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                    
                mode = scanner.options['mode']
                
                if not self.is_settable_option(mode):
                    reason = 'Unsettable \'mode\' option.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                
                if not mode.constraint_type == saneme.OPTION_CONSTRAINT_STRING_LIST:
                    reason = '\'Mode\' option does not include a STRING_LIST constraint.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                
                # Enforce resolution option requirements
                if not scanner.has_option('resolution'):
                    reason = 'No \'resolution\' option.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                    
                resolution = scanner.options['resolution']
                    
                if not self.is_settable_option(resolution):
                    reason = 'Unsettable \'resolution\' option.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                
                if resolution.constraint_type == saneme.OPTION_CONSTRAINT_NONE:
                    reason = '\'Resolution\' option does not specify a constraint.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
        
                # See SANE API 4.5.2
                if resolution.type != saneme.OPTION_TYPE_INT and \
                    resolution.type != saneme.OPTION_TYPE_FLOAT:
                    reason = '\'Resolution\' option is not of type INT or FLOAT.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                
                # See SANE API 4.5.2
                if not resolution.unit == saneme.OPTION_UNIT_DPI:
                    reason = '\'Resolution\' option is not measured in DPI units.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                    
                # Enforce scan area option requirements
                scan_area_option_names = ['tl-x', 'tl-y', 'br-x', 'br-y']
                
                supported = True
                for option_name in scan_area_option_names:
                    if not scanner.has_option(option_name):
                        supported = False
                        
                if not supported:
                    reason = 'No \'scan area\' options.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                
                scan_area_options = \
                    [scanner.options[o] for o in scan_area_option_names]
                
                supported = True
                for option in scan_area_options:
                    if option.type != saneme.OPTION_TYPE_INT:
                        supported = False
                        
                if not supported:
                    reason = '\'Scan area\' options are not of type INT.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue   
                
                supported = True
                for option in scan_area_options:
                    if option.unit != saneme.OPTION_UNIT_PIXEL and \
                        option.unit != saneme.OPTION_UNIT_MM:
                        supported = False
                        
                if not supported:
                    reason = '\'Scan area\' options are not measured in unit PIXEL or MM.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                                
                supported = True
                for option in scan_area_options:
                    if option.constraint_type != saneme.OPTION_CONSTRAINT_RANGE:
                        supported = False
                        
                if not supported:
                    reason = '\'Scan area\' options do not specify a RANGE constraint.'
                    self.log.info(unsupported_scanner_error % 
                        (scanner.display_name, reason))
                    new_unavailable_scanners.append((scanner.display_name, reason))
                    value.remove(scanner)
                    continue
                    
                scanner.close()   
            except saneme.SaneError:
                reason = 'Exception raised while attempting to query device options.'
                self.log.info(unsupported_scanner_error % 
                    (scanner.display_name, reason))
                new_unavailable_scanners.append((scanner.display_name, reason))
                value.remove(scanner)
                continue
        
        self._prop_unavailable_scanners = new_unavailable_scanners
        self._prop_available_scanners = value
        
        self.notify_property_value_change(
            'unavailable_scanners', None, new_unavailable_scanners)
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
    
    def set_prop_valid_page_sizes(self, value):
        # TODO
        pass
        
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
        
#    def state_scan_page_size_change(self):
#        """Read state, validating the input."""
#        state_manager = self.application.get_state_manager()
#        
#        if state_manager['scan_page_size'] in self.valid_page_sizes:
#            self.active_page_size = state_manager['scan_page_size']
#        else:
#            state_manager['scan_page_size'] = self.active_page_size

    # INTERNAL METHODS
    
    def is_settable_option(self, option):
        """
        Verify an option supports minimum capabilities needed to be used by
        NoStaples.
        """
        return option.is_active() and \
            option.is_soft_gettable() and \
            option.is_soft_settable()
            
    def _update_valid_modes(self):
        """
        Update valid modes from the active scanner.
        """
        self.valid_modes = self.active_scanner.options['mode'].constraint
    
    def _update_valid_resolutions(self):
        """
        Update valid resolutions from the active scanner.
        """
        if self.active_scanner.options['resolution'].constraint_type == \
            saneme.OPTION_CONSTRAINT_RANGE:
            min, max, step = self.active_scanner.options['resolution'].constraint
            
            # Fix for ticket #34.
            if step is None or step == 0:
                step = 1
            
            resolutions = []
            
            # If there are not an excessive number, include every possible
            # resolution
            if (max - min) / step <= constants.MAX_VALID_OPTION_VALUES:                
                i = min
                while i <= max:
                    resolutions.append(str(i))
                    i = i + step
            # Otherwise, take a crack at building a sensible set of options
            # that meet that constraint criteria
            else:
                # THE OLD METHOD: DID NOT WORK
#                    i = 1
#                    increment = (max - min) / (constants.MAX_VALID_OPTION_VALUES - 1)
#                    while (i <= constants.MAX_VALID_OPTION_VALUES - 2):
#                        unrounded = min + (i * increment)
#                        rounded = int(round(unrounded / step) * step)
#                        resolutions.append(str(rounded))
#                        i = i + 1
#                    resolutions.insert(0, str(min))
#                    resolutions.append(str(max))

                i = min
                tested_resolutions = []
                while i <= max:
                    try:
                        self.active_scanner.options['resolution'].value = i
                    except saneme.SANE_INFO_INEXACT:
                        pass
                    except saneme.SANE_INFO_RELOAD_PARAMS:
                        pass
                    
                    tested_resolutions.append(
                        self.active_scanner.options['resolution'].value)
                    i = i + step
                
                # Prune duplicates
                # http://code.activestate.com/recipes/52560/
                uniques = {}
                for j in tested_resolutions:
                    uniques[j] = True
                
                resolutions = [str(k) for k in uniques.keys()]
                
            self._prop_valid_resolutions = resolutions
        elif self.active_scanner.options['resolution'].constraint_type == \
            saneme.OPTION_CONSTRAINT_VALUE_LIST:                
            # Convert values to strings for display
            self.valid_resolutions = \
                [str(i) for i in self.active_scanner.options['resolution'].constraint]
        elif self.active_scanner.options['resolution'].constraint_type == \
            saneme.OPTION_CONSTRAINT_STRING_LIST:
            self.valid_resolutions = \
                self.active_scanner.options['resolution'].constraint
        else:
            raise AssertionError('Unsupported constraint type.')
    
    def _update_valid_page_sizes(self):
        """
        Update valid page sizes from the active scanner.
        """
        tl_x = self.active_scanner.options['tl-x']
        tl_y = self.active_scanner.options['tl-y']
        br_x = self.active_scanner.options['br-x']
        br_y = self.active_scanner.options['br-y']
        
        sizes = []
        resolution = int(self.active_resolution)
        
        # TODO - THIS SHOULD WORK, BE RESOLUTION NEEDS TO HAVE BEEN
        # PUSHED/UPDATED (FROM CONSTRAINT) BEFORE THIS IS VALID
        for name, size in constants.PAGESIZES.iteritems():
            if tl_x.unit == saneme.OPTION_UNIT_PIXEL:
                page_width = int(resolution * size[0] / points_per_inch)
                page_height = int(resolution * size[1] / points_per_inch)
                
                #print name, page_width, page_height
                
                if page_width < br_x.constraint[2] - tl_x.constraint[2] and \
                    page_height < br_y.constraint[2] - tl_y.cosntraint[2]:
                    sizes.append(name)
            elif tl_x.unit == saneme.OPTION_UNIT_MM:
                page_width = int(size[0] / (points_per_cm / 10))
                page_height = int(size[1] / (points_per_cm / 10))
                
                #print name, page_width, page_height
                
                if page_width < br_x.constraint[2] - tl_x.constraint[2] and \
                    page_height < br_y.constraint[2] - tl_y.cosntraint[2]:
                    sizes.append(name)                    
            else:
                raise AssertionError()
            
        print sizes
    
    def _reload_scanner_options(self):
        """
        Get current scanner options from the active_scanner.
        
        Useful for reloading any option that may have changed in response to
        a SaneReloadOptionsError.
        """
        main_controller = self.application.get_main_controller()
        
        self.log.debug('Reloading scanner options.')
        
        try:
            # Read updated values from the device
            new_mode = self.active_scanner.options['mode'].value
            new_resolution = str(self.active_scanner.options['resolution'].value)
            #new_page_size = ???
            
            # Reload valid options
            self._update_valid_modes()
            self._update_valid_resolutions()
            self._update_valid_page_sizes()
            
            # Reset new values (in case they were overwritten)
            self.active_mode = new_mode
            self.active_resolution = new_resolution
            #self.active_page_size = new_resolution
        except saneme.SaneError:
            exc_info = sys.exc_info()
            main_controller.run_device_exception_dialog(exc_info)
        
        self.log.debug('Scanner options reloaded.')