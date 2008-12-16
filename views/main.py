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
This module holds the MainView which exposes the application's main 
window.
"""

import logging
import os

import gtk
from gtkmvc.view import View

import constants
from views.document import DocumentView
from views.page import PageView

class MainView(View):
    """
    Exposes the application's main window.
    """

    def __init__(self, controller):
        """
        Constructs the MainView, including setting up controls that could
        not be configured in Glade and constructing sub-views.
        """
        scan_window_glade = os.path.join(
            constants.GUI_DIRECTORY, 'scan_window.glade')
        View.__init__(
            self, controller, scan_window_glade,
            'scan_window', None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Setup controls which can not be configured in Glade
        self['scan_window'].set_property('allow-shrink', True)

        self['scan_window_statusbar'].push(
            constants.STATUSBAR_BASE_CONTEXT_ID, 'Ready')
        
        # Setup sub views
        self.document_view = DocumentView(controller.document_controller)
        self.document_view['document_view_horizontal_box'].reparent(
             self['document_view_docking_viewport'])
        self['document_view_docking_viewport'].show_all()

        # All controls are disabled by default, they become
        # avaiable when an event indicates that they should be.
        self.set_scan_controls_sensitive(False)
        self.set_file_controls_sensitive(False)
        self.set_delete_controls_sensitive(False)
        self.set_zoom_controls_sensitive(False)
        self.set_adjustment_controls_sensitive(False)  
        self.set_navigation_controls_sensitive(False)
        
        controller.register_view(self)
        
        self.log.debug('Created.')
        
    def set_file_controls_sensitive(self, sensitive):
        """
        Enables or disables all gui widgets related to saving.
        """
        self['save_as_menu_item'].set_sensitive(sensitive)
        self['save_as_button'].set_sensitive(sensitive)
            
    def set_scan_controls_sensitive(self, sensitive):
        """
        Enables or disables all gui widgets related to scanning and
        setting of scanner options.
        """
        self['scan_menu_item'].set_sensitive(sensitive)
        self['insert_scan_menu_item'].set_sensitive(sensitive)
        self['scan_button'].set_sensitive(sensitive)
        
        self['scanner_menu_item'].set_sensitive(sensitive)
        #for child in self['scanner_sub_menu'].get_children():
        #    child.set_sensitive(sensitive)
            
        self['scan_mode_menu_item'].set_sensitive(sensitive)
        #for child in self['scan_mode_sub_menu'].get_children():
        #    child.set_sensitive(sensitive)
        
        self['scan_resolution_menu_item'].set_sensitive(sensitive)
        #for child in self['scan_resolution_sub_menu'].get_children():
        #    child.set_sensitive(sensitive)
            
    def set_delete_controls_sensitive(self, sensitive):
        """
        Enables or disables all gui widgets related to deleting or reordering 
        pages.
        """
        self['delete_menu_item'].set_sensitive(sensitive)
    
    def set_zoom_controls_sensitive(self, sensitive):
        """
        Enables or disables all gui widgets related to zooming.
        """
        self['zoom_in_menu_item'].set_sensitive(sensitive)
        self['zoom_out_menu_item'].set_sensitive(sensitive)
        self['zoom_one_to_one_menu_item'].set_sensitive(sensitive)
        self['zoom_best_fit_menu_item'].set_sensitive(sensitive)
        self['zoom_in_button'].set_sensitive(sensitive)
        self['zoom_out_button'].set_sensitive(sensitive)
        self['zoom_one_to_one_button'].set_sensitive(sensitive)
        self['zoom_best_fit_button'].set_sensitive(sensitive)
        
    def set_adjustment_controls_sensitive(self, sensitive):
        """
        Enables or disables all gui widgets related to making adjustments to 
        the current page.
        """
        self['rotate_counter_clockwise_menu_item'].set_sensitive(sensitive)
        self['rotate_clockwise_menu_item'].set_sensitive(sensitive)
        self['rotate_all_pages_menu_item'].set_sensitive(sensitive)
        self['rotate_counter_clockwise_button'].set_sensitive(sensitive)
        self['rotate_clockwise_button'].set_sensitive(sensitive)
        
        # TODO
        #self['brightness_scale'].set_sensitive(sensitive)
        #self['contrast_scale'].set_sensitive(sensitive)
        #self['sharpness_scale'].set_sensitive(sensitive)
        #self['color_all_pages_check'].set_sensitive(sensitive)

    def set_navigation_controls_sensitive(self, sensitive):
        """
        Enables or disables all gui widgets related to navigation.
        """
        self['go_first_menu_item'].set_sensitive(sensitive)
        self['go_previous_menu_item'].set_sensitive(sensitive)
        self['go_next_menu_item'].set_sensitive(sensitive)
        self['go_last_menu_item'].set_sensitive(sensitive)
        self['go_first_button'].set_sensitive(sensitive)
        self['go_previous_button'].set_sensitive(sensitive)
        self['go_next_button'].set_sensitive(sensitive)
        self['go_last_button'].set_sensitive(sensitive)