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
This module holds the PreferencesView which exposes user settings
through a dialog seperate from the main application window.
"""

import logging
import os

import gtk
from gtkmvc.view import View

from nostaples import constants
from nostaples.utils.gui import read_combobox, setup_combobox

class PreferencesView(View):
    """
    Exposes user settings through a dialog seperate from the main
    application window.
    """
    def __init__(self, application):
        """
        Constructs the PreferencesView, including setting up controls that 
        could not be configured in Glade.
        """
        self.application = application
        preferences_controller = application.get_preferences_controller()
        
        preferences_dialog_glade = os.path.join(
            constants.GUI_DIRECTORY, 'preferences_dialog.glade')
        View.__init__(
            self, preferences_controller, 
            preferences_dialog_glade, 'preferences_dialog', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Can not configure this via constructor do to the multiple
        # root windows in the Main View.
        self['preferences_dialog'].set_transient_for(
            application.get_main_view()['scan_window'])
        
        # These two combobox's are setup dynamically. Because of this they
        # must have their signal handlers connected manually.  Otherwise
        # their signals will fire before the view creation is finished.
        setup_combobox(
            self['preview_mode_combobox'],
            constants.PREVIEW_MODES_LIST, 
            application.get_preferences_model().preview_mode)
        
        self['preview_mode_combobox'].connect(
            'changed', 
            preferences_controller.on_preview_mode_combobox_changed)
        
        setup_combobox(
            self['thumbnail_size_combobox'],
            constants.THUMBNAIL_SIZE_LIST, 
            application.get_preferences_model().thumbnail_size)
        
        self['thumbnail_size_combobox'].connect(
            'changed', 
            preferences_controller.on_thumbnail_size_combobox_changed)
        
        setup_combobox(
            self['toolbar_style_combobox'],
            constants.TOOLBAR_STYLES_LIST, 
            application.get_preferences_model().toolbar_style)
        
        self['toolbar_style_combobox'].connect(
            'changed', 
            preferences_controller.on_toolbar_style_combobox_changed)
        
        # Setup the unavailable scanners tree view
        unavailable_liststore = gtk.ListStore(str)
        self['unavailable_tree_view'] = gtk.TreeView()
        self['unavailable_tree_view'].set_model(unavailable_liststore)
        self['unavailable_column'] = gtk.TreeViewColumn(None)
        self['unavailable_cell'] = gtk.CellRendererText()
        self['unavailable_tree_view'].append_column(self['unavailable_column'])
        self['unavailable_column'].pack_start(self['unavailable_cell'], True)        
        self['unavailable_column'].add_attribute(
            self['unavailable_cell'], 'text', 0)
        self['unavailable_tree_view'].get_selection().set_mode(
            gtk.SELECTION_NONE)
        self['unavailable_tree_view'].set_headers_visible(False)
        self['unavailable_tree_view'].set_property('can-focus', False)
        
        self['unavailable_scrolled_window'].add(self['unavailable_tree_view'])
        self['unavailable_scrolled_window'].show_all()
        
        # Setup the blacklist tree view
        blacklist_liststore = gtk.ListStore(str)
        self['blacklist_tree_view'] = gtk.TreeView()
        self['blacklist_tree_view'].set_model(blacklist_liststore)
        self['blacklist_column'] = gtk.TreeViewColumn(None)
        self['blacklist_cell'] = gtk.CellRendererText()
        self['blacklist_tree_view'].append_column(self['blacklist_column'])
        self['blacklist_column'].pack_start(self['blacklist_cell'], True)        
        self['blacklist_column'].add_attribute(self['blacklist_cell'], 'text', 0)
        self['blacklist_tree_view'].get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self['blacklist_tree_view'].set_headers_visible(False)
        self['blacklist_tree_view'].set_property('can-focus', False)
        
        self['blacklist_scrolled_window'].add(self['blacklist_tree_view'])
        self['blacklist_scrolled_window'].show_all()
        
        self['blacklist_tree_view'].get_selection().connect(
            'changed',
            preferences_controller.on_blacklist_tree_view_selection_changed)
        
        # Setup the available devices tree view
        available_liststore = gtk.ListStore(str)
        self['available_tree_view'] = gtk.TreeView()
        self['available_tree_view'].set_model(available_liststore)
        self['available_column'] = gtk.TreeViewColumn(None)
        self['available_cell'] = gtk.CellRendererText()
        self['available_tree_view'].append_column(self['available_column'])
        self['available_column'].pack_start(self['available_cell'], True)        
        self['available_column'].add_attribute(self['available_cell'], 'text', 0)
        self['available_tree_view'].get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self['available_tree_view'].set_headers_visible(False)
        self['available_tree_view'].set_property('can-focus', False)
        
        self['available_scrolled_window'].add(self['available_tree_view'])
        self['available_scrolled_window'].show_all()
        
        self['available_tree_view'].get_selection().connect(
            'changed',
            preferences_controller.on_available_tree_view_selection_changed)
        
        # Setup the keywords tree view
        keywords_liststore = gtk.ListStore(str)
        self['keywords_tree_view'] = gtk.TreeView()
        self['keywords_tree_view'].set_model(keywords_liststore)
        self['keywords_column'] = gtk.TreeViewColumn(None)
        self['keywords_cell'] = gtk.CellRendererText()
        self['keywords_tree_view'].append_column(self['keywords_column'])
        self['keywords_column'].pack_start(self['keywords_cell'], True)        
        self['keywords_column'].add_attribute(self['keywords_cell'], 'text', 0)
        self['keywords_tree_view'].get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self['keywords_tree_view'].set_headers_visible(False)
        self['keywords_tree_view'].set_property('can-focus', False)
        
        self['keywords_scrolled_window'].add(self['keywords_tree_view'])
        self['keywords_scrolled_window'].show_all()
        
        application.get_preferences_controller().register_view(self)
        
        self.log.debug('Created.')
        
    def run(self):
        """Run the modal preferences dialog."""
        self['preferences_dialog'].run()