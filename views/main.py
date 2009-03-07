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

from nostaples import constants

class MainView(View):
    """
    Exposes the application's main window.
    """

    def __init__(self, application):
        """
        Constructs the MainView, including setting up controls that could
        not be configured in Glade and constructing sub-views.
        """        
        self.application = application
        scan_window_glade = os.path.join(
            constants.GUI_DIRECTORY, 'scan_window.glade')
        View.__init__(
            self, application.get_main_controller(), 
            scan_window_glade, ['scan_window', 'progress_window'], 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Setup controls which can not be configured in Glade
        self['scan_window'].set_geometry_hints(min_width=600, min_height=400)
        
        # Setup sub views
        document_view = self.application.get_document_view()
        document_view['document_view_horizontal_box'].reparent(
             self['document_view_docking_viewport'])
        self['document_view_docking_viewport'].show_all()
        
        status_view = self.application.get_status_view()
        status_view['statusbar'].reparent(
             self['status_view_docking_viewport'])
        self['status_view_docking_viewport'].show_all()

        # All controls are disabled by default, they become
        # avaiable when an event indicates that they should be.
        self.set_scan_controls_sensitive(False)
        self.set_file_controls_sensitive(False)
        self.set_delete_controls_sensitive(False)
        self.set_zoom_controls_sensitive(False)
        self.set_adjustment_controls_sensitive(False)
        self.set_navigation_controls_sensitive(False)
        document_view.set_adjustments_sensitive(False)
        
        application.get_main_controller().register_view(self)
        
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
        self['scan_button'].set_sensitive(sensitive)
        
        self['scanner_menu_item'].set_sensitive(sensitive)
        self['scan_mode_menu_item'].set_sensitive(sensitive)
        self['scan_resolution_menu_item'].set_sensitive(sensitive)
        
    def set_refresh_scanner_controls_sensitive(self, sensitive):
        """
        Enable or disable all gui widgets related to refreshing the
        available hardware for scanning.
        """
        self['refresh_available_scanners_menu_item'].set_sensitive(sensitive)  
        self['refresh_available_scanners_button'].set_sensitive(sensitive)         
            
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
        
        self.application.get_document_view().set_adjustments_sensitive(sensitive)

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
        
    def run_device_exception_dialog(self, exc_info):
        """
        Display an error dialog that provides the user with the option of
        blacklisting the device which caused the error.
        
        TODO: Rebuild dialog in Glade.
        """
        dialog = gtk.MessageDialog(
            parent=None, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_NONE)
        dialog.set_title('')
    
        primary = "<big><b>A hardware exception has been logged.</b></big>"
        secondary = '<b>Device:</b> %s\n<b>Exception:</b> %s\n\n%s' % (
            exc_info[1].device.display_name,
            exc_info[1].message, 
            'If this error continues to occur you may choose to blacklist the device so that it no longer appears in the list of available scanners.')
    
        dialog.set_markup(primary)
        dialog.format_secondary_markup(secondary)
    
        dialog.add_button('Blacklist Device', constants.RESPONSE_BLACKLIST_DEVICE)
        dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
    
        response = dialog.run()        
        dialog.destroy()
        
        return response