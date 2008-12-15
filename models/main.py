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
from models.adjustments import AdjustmentsModel
from models.document import DocumentModel
from models.page import PageModel
from models.preferences import PreferencesModel
from models.save import SaveModel
from state import StateManager

class MainModel(Model):
    """
    Handles data all data not specifically handled by another Model 
    (e.g. the state of the main application window).
    
    # TODO: persist active_scanner to gconf.
        move scanner loading logic into model as much as possible
        when loading active_scanner (the string) changes, check for its existence in
            available_scanners and update as necessary
        the controller should also be taking its queues for the active_scanner from
            this model, rather than making its own determination
        accomplish both these things and the view should be able to update smoothly
            whether the change came from user input or from a change in gconf
    """
    __properties__ = \
    {
        'show_toolbar' : True,
        'show_statusbar' : True,
        'show_thumbnails' : True,
        'show_adjustments' : False,
        'available_scanners' : [], # Tuples: (display_name, sane_name)
        'active_scanner' : None, # Tuple, also
        'valid_modes' : [],
        'valid_resolutions' : [],
        'active_mode' : None,
        'active_resolution' : None,
        'is_scanner_in_use' : True,
        'is_document_empty' : True,
    }

    def __init__(self):
        """
        Constructs the MainModel, as well as necessary sub-models.
        """
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Sub-models
        self.adjustments_model = AdjustmentsModel()
        self.document_model = DocumentModel()
        self.document_model.register_observer(self)
        self.preferences_model = PreferencesModel()
        self.save_model = SaveModel()
        
        # TODO: Wtf am I doing here, solves a bug, but why?
        self.accepts_spurious_change = lambda : True
        
        self.log.debug('Created.')
        
    def load_state(self):
        """
        Load persisted state from the StateManager.
        """
        self.show_toolbar = StateManager.init_state(
            'show_toolbar', constants.DEFAULT_SHOW_TOOLBAR, 
            self.state_show_toolbar_change)
        
        self.show_statusbar = StateManager.init_state(
            'show_statusbar', constants.DEFAULT_SHOW_STATUSBAR, 
            self.state_show_statusbar_change)
        
        self.show_thumbnails = StateManager.init_state(
            'show_thumbnails', constants.DEFAULT_SHOW_THUMBNAILS, 
            self.state_show_thumbnails_change)
        
        self.show_adjustments = StateManager.init_state(
            'show_adjustments', constants.DEFAULT_SHOW_ADJUSTMENTS, 
            self.state_show_adjustments_change)

        self._prop_active_scanner = StateManager.init_state(
            'active_scanner', constants.DEFAULT_ACTIVE_SCANNER, 
            self.state_active_scanner_change)
        
        self._prop_active_mode = StateManager.init_state(
            'scan_mode', constants.DEFAULT_SCAN_MODE, 
            self.state_scan_mode_change)
        
        self._prop_active_resolution = StateManager.init_state(
            'scan_resolution', constants.DEFAULT_SCAN_RESOLUTION, 
            self.state_scan_resolution_change)
        
    # Property setters
    # (see gtkmvc.support.metaclass_base.py for the origin of these accessors)
    
    def set_prop_show_toolbar(self, value):
        """Write state."""
        old_value = self._prop_show_toolbar
        self._prop_show_toolbar = value
        StateManager['show_toolbar'] = value
        self.notify_property_value_change(
            'show_toolbar', old_value, value)
    
    def set_prop_show_statusbar(self, value):
        """Write state."""
        old_value = self._prop_show_statusbar
        self._prop_show_statusbar = value
        StateManager['show_statusbar'] = value
        self.notify_property_value_change(
            'show_statusbar', old_value, value)
    
    def set_prop_show_thumbnails(self, value):
        """Write state."""
        old_value = self._prop_show_thumbnails
        self._prop_show_thumbnails = value
        StateManager['show_thumbnails'] = value
        self.notify_property_value_change(
            'show_thumbnails', old_value, value)
    
    def set_prop_show_adjustments(self, value):
        """Write state."""
        old_value = self._prop_show_adjustments
        self._prop_show_adjustments = value
        StateManager['show_adjustments'] = value
        self.notify_property_value_change(
            'show_adjustments', old_value, value)
        
    def set_prop_active_scanner(self, value):
        """Write state."""
        old_value = self._prop_active_scanner
        self._prop_active_scanner = value
        if value is not None:
            StateManager['active_scanner'] = value
        self.notify_property_value_change(
            'active_scanner', old_value, value)
        
    def set_prop_active_mode(self, value):
        """Write state."""
        old_value = self._prop_active_mode
        self._prop_active_mode = value
        if value is not None:
            StateManager['scan_mode'] = value
        self.notify_property_value_change(
            'active_mode', old_value, value)
        
    def set_prop_active_resolution(self, value):
        """Write state."""
        old_value = self._prop_active_resolution
        self._prop_active_resolution = value
        if value is not None:
            StateManager['scan_resolution'] = value
        self.notify_property_value_change(
            'active_resolution', old_value, value)
        
#    def property_available_scanners_value_change(self, model, old_value, new_value):
#        """
#        TODO
#        """        
#        if len(list(new_value)) == 0:
#            self.active_scanner = self.null_scanner
#        else:                   
#            # Select the first scanner if the previously selected scanner
#            # is not in the list
#            if self.active_scanner not in self.model.available_scanners:
#                self.active_scanner = self.model.available_scanners[0]    
        
    # State callbacks
    
    def state_show_toolbar_change(self):
        """Read state."""
        self.show_toolbar = StateManager['show_toolbar']
    
    def state_show_statusbar_change(self):
        """Read state."""
        self.show_statusbar = StateManager['show_statusbar']
    
    def state_show_thumbnails_change(self):
        """Read state."""
        self.show_thumbnails = StateManager['show_thumbnails']
    
    def state_show_adjustments_change(self):
        """Read state."""
        self.show_adjustments = StateManager['show_adjustments']
        
    def state_active_scanner_change(self):
        """Read state, validating the input."""
        if StateManager['active_scanner'] in self.available_scanners:
            self.active_scanner = StateManager['active_scanner']
        else:
            StateManager['active_scanner'] = self.active_scanner
        
    def state_scan_mode_change(self):
        """Read state, validating the input."""
        if StateManager['scan_mode'] in self.valid_modes:
            self.active_mode = StateManager['scan_mode']
        else:
            StateManager['scan_mode'] = self.active_mode
        
    def state_scan_resolution_change(self):
        """Read state, validating the input."""
        if StateManager['scan_resolution'] in self.valid_resolutions:
            self.active_resolution = StateManager['scan_resolution']
        else:
            StateManager['scan_resolution'] = self.active_resolution
     
    # ScannerModel PROPERTY CALLBACKS
        
    def property_active_mode_value_change(self, model, old_value, new_value):
        """Write state"""
        StateManager['scan_mode'] = new_value
        
    def property_active_resolution_value_change(self, model, old_value, new_value):
        """Write state"""
        StateManager['scan_resolution'] = new_value 

    # DocumentModel PROPERTY CALLBACKS
    
    def property_count_value_change(self, model, old_value, new_value):
        """
        Toggle whether or not the document is empty.
        """
        if new_value == 0:
            self.is_document_empty = True
        else:
            self.is_document_empty = False