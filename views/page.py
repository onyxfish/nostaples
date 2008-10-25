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
TODO
"""

import logging

import gtk
from gtkmvc.view import View

import constants

class PageView(View):
    """
    TODO
    """
    def __init__(self, controller):
        View.__init__(
            self, controller, constants.GLADE_CONFIG, 'preview_table',
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)

        self['preview_horizontal_scrollbar'].set_adjustment(
            self['preview_layout'].get_hadjustment())
        self['preview_vertical_scrollbar'].set_adjustment(
            self['preview_layout'].get_vadjustment())
        
        self['preview_layout'].modify_bg(
            gtk.STATE_NORMAL, 
            gtk.gdk.colormap_get_system().alloc_color(
                gtk.gdk.Color(0, 0, 0), False, True))
        
        controller.register_view(self)
        
        self.log.debug('Created.')
