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
This module holds the View for the main application window.
"""

import logging

import gtk
from gtkmvc.view import View

import constants
from page import PageView
from thumbnails import ThumbnailsView

class MainView(View):
    """
    The main view on the application--generally speaking, the 
    scan_window.
    """

    def __init__(self, controller):
        View.__init__(
            self, controller, constants.GLADE_CONFIG, 'scan_window', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Setup controls which can not be configured in Glade
        self['scan_window'].set_property('allow-shrink', True)

        self['scan_window_statusbar'].push(
            constants.STATUSBAR_BASE_CONTEXT_ID, 'Ready')
        
        # Setup sub views
        self.thumbnails_view = ThumbnailsView( 
            controller.thumbnails_controller)
            
        self['thumbnails_scrolled_window'].add(
            self.thumbnails_view['thumbnails_tree_view'])
        self['thumbnails_scrolled_window'].show_all()
        
        self.page_view = PageView(
            controller.page_controller)
        
        self['preview_viewport'].add(self.page_view['preview_table'])
        
#        if self.app.state_manager['show_toolbar'] == False:
#            self.show_toolbar_menu_item.set_active(False)
#            self.toolbar.hide()
#        
#        if self.app.state_manager['show_thumbnails'] == False:
#            self.show_thumbnails_menu_item.set_active(False)
#            self.thumbnails_scrolled_window.hide()
#        
#        if self.app.state_manager['show_statusbar'] == False:
#            self.show_statusbar_menu_item.set_active(False)
#            self.statusbar.hide()
        
        controller.register_view(self)
        
        self.log.debug('Created.')
