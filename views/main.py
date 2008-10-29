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
        View.__init__(
            self, controller, constants.GLADE_CONFIG, 
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
