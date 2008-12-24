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

import constants

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
        
        'active_scanner' : None,
        'active_mode' : None,
        'active_resolution' : None,
        
        'available_scanners' : [],
        'valid_modes' : [],
        'valid_resolutions' : [],
        
        'scan_in_progress' : False,
        'updating_available_scanners' : False,
        'updating_scan_options' : False,
        
        'is_document_empty' : True,
        'is_document_multiple_pages': False,
    }

    def __init__(self, application):
        """
        Constructs the MainModel, as well as necessary sub-models.
        """
        self.application = application
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        # TODO: this is WRONG, the MainController should be the observing class
        application.get_document_model().register_observer(self)
        
        self.log.debug('Created.')
        
    def load_state(self):
        """
        Load persisted state from the self.state_manager.
        """
        state_manager = self.application.get_state_manager()
        
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

        self._prop_active_scanner = state_manager.init_state(
            'active_scanner', constants.DEFAULT_ACTIVE_SCANNER, 
            self.state_active_scanner_change)
        
        self._prop_active_mode = state_manager.init_state(
            'scan_mode', constants.DEFAULT_SCAN_MODE, 
            self.state_scan_mode_change)
        
        self._prop_active_resolution = state_manager.init_state(
            'scan_resolution', constants.DEFAULT_SCAN_RESOLUTION, 
            self.state_scan_resolution_change)
        
    # Property setters
    # (see gtkmvc.support.metaclass_base.py for the origin of these accessors)
    
    def set_prop_show_toolbar(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_show_toolbar
        if old_value == value:
            return
        self._prop_show_toolbar = value
        self.application.get_state_manager()['show_toolbar'] = value
        self.notify_property_value_change(
            'show_toolbar', old_value, value)
    
    def set_prop_show_statusbar(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_show_statusbar
        if old_value == value:
            return
        self._prop_show_statusbar = value
        self.application.get_state_manager()['show_statusbar'] = value
        self.notify_property_value_change(
            'show_statusbar', old_value, value)
    
    def set_prop_show_thumbnails(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_show_thumbnails
        if old_value == value:
            return
        self._prop_show_thumbnails = value
        self.application.get_state_manager()['show_thumbnails'] = value
        self.notify_property_value_change(
            'show_thumbnails', old_value, value)
    
    def set_prop_show_adjustments(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        old_value = self._prop_show_adjustments
        if old_value == value:
            return
        self._prop_show_adjustments = value
        self.application.get_state_manager()['show_adjustments'] = value
        self.notify_property_value_change(
            'show_adjustments', old_value, value)
        
    def set_prop_active_scanner(self, value):
        """
        Write state.
        See L{set_prop_active_scanner} for detailed comments.
        """
        # Ignore spurious updates
        old_value = self._prop_active_scanner
        if old_value == value:
            return
        
        # Update the internal property variable
        self._prop_active_scanner = value
        
        # Only persist the state if the new value is not None
        # This prevents problems with trying to store a Null
        # value in the state backend and also allows for smooth
        # transitions if a scanner is disconnecte and reconnected.
        if value is not None:
            self.application.get_state_manager()['active_scanner'] = value
            
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
                self._prop_active_scanner = value[0]
                self.application.get_state_manager()['active_scanner'] = value[0]
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
                self.application.get_state_manager()['scan_resolution'] = value[0]
            else:
                pass
        
        self._prop_valid_resolutions = value
        
        self.notify_property_value_change(
            'valid_resolutions', old_value, value)
        
        self.notify_property_value_change(
            'active_resolution', None, self._prop_active_resolution)
        
    # State callbacks
    
    def state_show_toolbar_change(self):
        """Read state."""
        self.show_toolbar = self.application.get_state_manager()['show_toolbar']
    
    def state_show_statusbar_change(self):
        """Read state."""
        self.show_statusbar = self.application.get_state_manager()['show_statusbar']
    
    def state_show_thumbnails_change(self):
        """Read state."""
        self.show_thumbnails = self.application.get_state_manager()['show_thumbnails']
    
    def state_show_adjustments_change(self):
        """Read state."""
        self.show_adjustments = self.application.get_state_manager()['show_adjustments']
        
    def state_active_scanner_change(self):
        """Read state, validating the input."""
        if self.application.get_state_manager()['active_scanner'] in self.available_scanners:
            self.active_scanner = self.application.get_state_manager()['active_scanner']
        else:
            self.application.get_state_manager()['active_scanner'] = self.active_scanner
        
    def state_scan_mode_change(self):
        """Read state, validating the input."""
        if self.application.get_state_manager()['scan_mode'] in self.valid_modes:
            self.active_mode = self.application.get_state_manager()['scan_mode']
        else:
            self.application.get_state_manager()['scan_mode'] = self.active_mode
        
    def state_scan_resolution_change(self):
        """Read state, validating the input."""
        if self.application.get_state_manager()['scan_resolution'] in self.valid_resolutions:
            self.active_resolution = self.application.get_state_manager()['scan_resolution']
        else:
            self.application.get_state_manager()['scan_resolution'] = self.active_resolution

    # DocumentModel PROPERTY CALLBACKS
    
    def property_count_value_change(self, model, old_value, new_value):
        """
        Toggle whether or not the document is empty.
        """        
        if new_value == 0:
            self.is_document_empty = True
            self.is_document_multiple_pages = False
        elif new_value == 1:
            self.is_document_empty = False
            self.is_document_multiple_pages = False
        else:
            self.is_document_empty = False
            self.is_document_multiple_pages = True