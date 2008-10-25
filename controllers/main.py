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

'''
This module holds the controller for the main application view and
model.
'''

import logging

import gtk
from gtkmvc.controller import Controller

from page import PageController
from thumbnails import ThumbnailsController

class MainController(Controller):
    '''
    '''
    def __init__(self, model):
        Controller.__init__(self, model)
        
        self.page_controller = PageController(model.blank_page)
        
        self.thumbnails_controller = ThumbnailsController(
            model.thumbnails_model)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def quit(self):
        self.log.debug('Quit.')
        gtk.main_quit()
        
    def on_scan_window_destroy(self, window):
        self.quit()
        
    def on_quit_menu_item_activate(self, menu_item):
        self.quit()
