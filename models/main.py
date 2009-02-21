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

from gtkmvc.model import Model

from nostaples import constants
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
            self.state_show_toolbar_change)
        
        self.show_statusbar = state_manager.init_state(
            'show_statusbar', constants.DEFAULT_SHOW_STATUSBAR, 
            self.state_show_statusbar_change)
        
        self.show_thumbnails = state_manager.init_state(
            'show_thumbnails', constants.DEFAULT_SHOW_THUMBNAILS, 
            self.state_show_thumbnails_change)
        
        self.show_adjustments = state_manager.init_state(
            'show_adjustments', constants.DEFAULT_SHOW_ADJUSTMENTS, 
            self.state_show_adjustments_change)
        
        self.rotate_all_pages = state_manager.init_state(
            'rotate_all_pages', constants.DEFAULT_ROTATE_ALL_PAGES, 
            self.state_rotate_all_pages_change)

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
        
    # Property setters
    # (see gtkmvc.support.metaclass_base.py for the origin of these accessors)
    
    class GenericPropertySetter(object):
        """
        This 'function factory' produces callable objects
        to override the python-gtkmvc accessors established in
        gtkmvc.support.metaclass_base.py.
        
        These functions not only handle notifying observers
        of changes in the property, but also persist changes
        to the gconf backend.
        """
        def __init__(self, property_name, state_name):
            """
            Store the property name which is visible to the
            application as well as its attribute name.
            """
            self.property_name = property_name
            self.state_name = state_name
            self.property_attr_name = '_prop_%s' % self.property_name
        
        def __call__(self, cls, value):
            """
            Write state to gconf and notify observers of changes.
            
            For more details on how this works see
            L{set_prop_active_scanner}.
            """
            old_value = getattr(cls, self.property_attr_name)
            if old_value == value:
                return
            setattr(cls, self.property_attr_name, value)
            cls.application.get_state_manager()[self.state_name] = value
            cls.notify_property_value_change(
                self.property_name, old_value, value)
    
    set_prop_show_toolbar = GenericPropertySetter('show_toolbar', 'show_toolbar')
    set_prop_show_statusbar = GenericPropertySetter('show_statusbar', 'show_statusbar')
    set_prop_show_thumbnails = GenericPropertySetter('show_thumbnails', 'show_thumbnails')
    set_prop_show_adjustments = GenericPropertySetter('show_adjustments', 'show_adjustments')
    set_prop_rotate_all_pages = GenericPropertySetter('rotate_all_pages', 'rotate_all_pages')
        
    def set_prop_active_scanner(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        main_controller = self.application.get_main_controller()
        
        # Ignore spurious updates
        old_value = self._prop_active_scanner
        if old_value == value:
            return
        
        # Close the old scanner
        old_value.close()
        
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
            # TODO: handle exceptions
            try:
                value.open()
            except saneme.SaneError, e:
                main_controller.display_device_exception_dialog(e)
            
            self.application.get_state_manager()['active_scanner'] = value.name
            
        # Emit the property change notification to all observers.
        self.notify_property_value_change(
            'active_scanner', old_value, value)
        
    def set_prop_active_mode(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_active_mode
        if old_value == value:
            return        
        self._prop_active_mode = value        
        if value is not None:
            self.application.get_state_manager()['scan_mode'] = value            
        self.notify_property_value_change(
            'active_mode', old_value, value)
        
    def set_prop_active_resolution(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_active_resolution
        if old_value == value:
            return
        self._prop_active_resolution = value
        if value is not None:
            self.application.get_state_manager()['scan_resolution'] = value
        self.notify_property_value_change(
            'active_resolution', old_value, value)
        
    def set_prop_available_scanners(self, value):
        """
        Set the list of available scanners, updating the active_scanner
        if it is no longer in the list.
        """
        main_controller = self.application.get_main_controller()
        
        old_value = self._prop_available_scanners
        
        if len(value) == 0:
            self._prop_active_scanner = None
        else:           
            # Select the first available scanner if the previously 
            # selected scanner is not in the new list
            # We avoid the active_scanner property setter so that
            # The property notification callbacks will not be fired
            # until after the menu has been updated.
            if self._prop_active_scanner not in value:
                try:
                    value[0].open()
                    
                    self._prop_active_scanner = value[0]
                    self.application.get_state_manager()['active_scanner'] = \
                        value[0].name
                except saneme.SaneError, e:
                    main_controller.display_device_exception_dialog(e)
            # Otherwise maintain current selection
            else:
                pass
        
        self._prop_available_scanners = value
        
        # This will only actually cause an update if
        # old_value != value
        self.notify_property_value_change(
            'available_scanners', old_value, value)
        
        # Force the scanner options to update, even if the active
        # scanner did not change.  This is necessary in case the 
        # current value was loaded from state, in which case the 
        # options will not yet have been loaded).
        self.notify_property_value_change(
            'active_scanner', None, self._prop_active_scanner)
        
    def set_prop_valid_modes(self, value):
        """
        Set the list of valid scan modes, updating the active_mode
        if it is no longer in the list.
        
        See L{set_prop_available_scanners} for detailed comments.
        """
        old_value = self._prop_valid_modes
        
        if len(value) == 0:
            self._prop_active_mode = None
        else:
            if self._prop_active_mode not in value:
                self._prop_active_mode = value[0]
                self.application.get_state_manager()['scan_mode'] = value[0]
            else:
                pass
        
        self._prop_valid_modes = value
        
        self.notify_property_value_change(
            'valid_modes', old_value, value)
        
        self.notify_property_value_change(
            'active_mode', None, self._prop_active_mode)
        
    def set_prop_valid_resolutions(self, value):
        """
        Set the list of valid scan resolutions, updating the 
        active_resolution if it is no longer in the list.
        
        See L{set_prop_available_scanners} for detailed comments.
        """
        old_value = self._prop_valid_resolutions
        
        if len(value) == 0:
            self._prop_active_resolution = None
        else:
            if self._prop_active_resolution not in value:
                self._prop_active_resolution = value[0]
                self.application.get_state_manager()['scan_resolution'] = \
                    value[0]
            else:
                pass
        
        self._prop_valid_resolutions = value
        
        self.notify_property_value_change(
            'valid_resolutions', old_value, value)
        
        self.notify_property_value_change(
            'active_resolution', None, self._prop_active_resolution)
        
    # STATE CALLBACKS
       
    def state_show_toolbar_change(self):
        """Read state."""
        self.show_toolbar = \
            self.application.get_state_manager()['show_toolbar']
            
    def state_show_statusbar_change(self):
        """Read state."""
        self.show_statusbar = \
            self.application.get_state_manager()['show_statusbar']
            
    def state_show_thumbnails_change(self):
        """Read state."""
        self.show_thumbnails = \
            self.application.get_state_manager()['show_thumbnails']   
    
    def state_show_adjustments_change(self):
        """Read state."""
        self.show_adjustments = \
            self.application.get_state_manager()['show_adjustments']
    
    def state_rotate_all_pages_change(self):
        """Read state."""
        self.rotate_all_pages = \
            self.application.get_state_manager()['rotate_all_pages']
        
    def state_active_scanner_change(self):
        """Read state, validating the input."""
        state_manager = self.application.get_state_manager()
        sane = self.application.get_sane()
        
        if state_manager['active_scanner'] in self.available_scanners:
            try:
                self.active_scanner = sane.get_device_by_name(state_manager['active_scanner'])
            except SaneNoSuchDeviceError:
                raise
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