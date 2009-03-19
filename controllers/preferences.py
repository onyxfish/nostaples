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
This module holds the L{PreferencesController}, which manages interaction 
between the L{PreferencesModel} and L{PreferencesView}.
"""

import logging

import gtk
from gtkmvc.controller import Controller

from nostaples import constants
from nostaples.utils.gui import read_combobox

class PreferencesController(Controller):
    """
    Manages interaction between the L{PreferencesModel} and 
    L{PreferencesView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the PreferencesController.
        """
        self.application = application
        Controller.__init__(self, application.get_preferences_model())
        
        application.get_main_model().register_observer(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def register_adapters(self):
        """
        Registers adapters for property/widget pairs that do not require 
        complex processing.
        """
        pass
    
    # USER INTERFACE CALLBACKS
    
    def on_preview_mode_combobox_changed(self, combobox):
        """Update the preview mode in the PreferencesModel."""
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        preferences_model.preview_mode = \
            read_combobox(preferences_view['preview_mode_combobox'])
    
    def on_thumbnail_size_combobox_changed(self, combobox):
        """Update the thumbnail size in the PreferencesModel."""
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        preferences_model.thumbnail_size = \
            int(read_combobox(preferences_view['thumbnail_size_combobox']))
            
    def on_toolbar_style_combobox_changed(self, combobox):
        """Update the toolbar style in the PreferencesModel."""
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        preferences_model.toolbar_style = \
            read_combobox(preferences_view['toolbar_style_combobox'])
            
    def on_remove_from_blacklist_button_clicked(self, button):
        """
        Remove the currently selected blacklist device from the list.
        """
        main_controller = self.application.get_main_controller()
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        model, selection_iter = \
            preferences_view['blacklist_tree_view'].get_selection().get_selected()
            
        if not selection_iter:
            return
            
        selection_text = model.get_value(selection_iter, 0)
        model.remove(selection_iter)
        
        temp_blacklist = list(preferences_model.blacklisted_scanners)
        temp_blacklist.remove(selection_text)
        preferences_model.blacklisted_scanners = temp_blacklist
        
        main_controller._update_available_scanners()
            
    def on_add_to_blacklist_button_clicked(self, button):
        """
        Move the currently selected available scanner to the blacklist.
        """
        main_controller = self.application.get_main_controller()
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        model, selection_iter = \
            preferences_view['available_tree_view'].get_selection().get_selected()
            
        if not selection_iter:
            return
            
        selection_text = model.get_value(selection_iter, 0)
        model.remove(selection_iter)
        
        temp_blacklist = list(preferences_model.blacklisted_scanners)
        temp_blacklist.append(selection_text)
        preferences_model.blacklisted_scanners = temp_blacklist
        
        main_controller._update_available_scanners()
    
    def on_remove_from_keywords_button_clicked(self, button):
        """
        Remove the currently selected keyword from the list.
        """
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        model, selection_iter = \
            preferences_view['keywords_tree_view'].get_selection().get_selected()
            
        if not selection_iter:
            return
        
        selection_text = model.get_value(selection_iter, 0)
        model.remove(selection_iter)
        
        temp_keywords = list(preferences_model.saved_keywords)
        temp_keywords.remove(selection_text)
        preferences_model.saved_keywords = temp_keywords
        
    def on_blacklist_tree_view_selection_changed(self, selection):
        """Update the available device controls."""
        self._toggle_device_controls()  
        
    def on_available_tree_view_selection_changed(self, selection):
        """Update the available device controls."""
        self._toggle_device_controls()  

    def on_preferences_dialog_response(self, dialog, response):
        """Close the preferences dialog."""
        preferences_view = self.application.get_preferences_view()
        
        preferences_view['preferences_dialog'].hide()
        
    # PROPERTY CALLBACKS
    
    def property_preview_mode_value_change(self, model, old_value, new_value):
        # TODO - set the combobox (in case the change came form state)
        pass
    
    def property_thumbnail_size_value_change(self, model, old_value, new_value):
        # TODO - set the combobox (in case the change came form state)
        pass
    
    def property_toolbar_style_value_change(self, model, old_value, new_value):
        # TODO - set the combobox (in case the change came form state)
        pass
    
    def property_blacklisted_scanners_value_change(self, model, old_value, new_value):
        """Update blacklisted scanners liststore."""
        preferences_view = self.application.get_preferences_view()
        
        blacklist_liststore = preferences_view['blacklist_tree_view'].get_model()
        blacklist_liststore.clear()
        
        for blacklist_item in new_value:
            blacklist_liststore.append([blacklist_item])
            
        self._toggle_device_controls()
            
    def property_saved_keywords_value_change(self, model, old_value, new_value):
        """Update keywords liststore."""
        preferences_view = self.application.get_preferences_view()
        
        keywords_liststore = preferences_view['keywords_tree_view'].get_model()
        keywords_liststore.clear()
        
        for keyword in new_value:
            keywords_liststore.append([keyword])
        
    # MainModel PROPERTY CALLBACKS
    
    def property_available_scanners_value_change(self, model, old_value, new_value):
        """Update available scanners liststore."""
        preferences_view = self.application.get_preferences_view()
        
        available_liststore = preferences_view['available_tree_view'].get_model()
        available_liststore.clear()
        
        for available_item in new_value:
            available_liststore.append([available_item.display_name])
            
        self._toggle_device_controls()  
    
    def property_unavailable_scanners_value_change(self, model, old_value, new_value):
        """Update unavailable scanners liststore."""
        preferences_view = self.application.get_preferences_view()
        
        unavailable_liststore = preferences_view['unavailable_tree_view'].get_model()
        unavailable_liststore.clear()
        
        for unavailable_item in new_value:
            unavailable_liststore.append([unavailable_item[0]])
            
    def property_updating_available_scanners_value_change(self, model, old_value, new_value):
        """
        Disable device management controls while devices are being updated.
        """
        self._toggle_device_controls()
    
    # PUBLIC METHODS
    
    def run(self):
        """Run the preferences dialog."""
        main_model = self.application.get_main_model()
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()
        
        # Force property updates when dialog is run: this handles the case
        # where the PreferencesController has not been created until now
        # so it has not been receiving property notifications.
        self.property_blacklisted_scanners_value_change(
            preferences_model, None, preferences_model.blacklisted_scanners)
        self.property_saved_keywords_value_change(
            preferences_model, None, preferences_model.saved_keywords)
        self.property_available_scanners_value_change(
            main_model, None, main_model.available_scanners)
        self.property_unavailable_scanners_value_change(
            preferences_model, None, main_model.unavailable_scanners)
        
        preferences_view.run()
        
    # PRIVATE METHODS
    
    def _toggle_device_controls(self):
        """
        Toggle the availability of the scanner management controls based on
        the state of the application.
        """
        main_model = self.application.get_main_model()
        preferences_model = self.application.get_preferences_model()
        preferences_view = self.application.get_preferences_view()        
        
        if main_model.updating_available_scanners:
            preferences_view['remove_from_blacklist_button'].set_sensitive(False)
            preferences_view['add_to_blacklist_button'].set_sensitive(False)
        else:
            if preferences_view['blacklist_tree_view'].get_selection().count_selected_rows() > 0:
            #if len(preferences_model.blacklisted_scanners) > 0:
                preferences_view['remove_from_blacklist_button'].set_sensitive(True)
            else:
                preferences_view['remove_from_blacklist_button'].set_sensitive(False)
                
            if preferences_view['available_tree_view'].get_selection().count_selected_rows() > 0:
            #if len(main_model.available_scanners) > 0:
                preferences_view['add_to_blacklist_button'].set_sensitive(True)
            else:
                preferences_view['add_to_blacklist_button'].set_sensitive(False)
                