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
This module holds the PageView which exposes the scanned page that is
currently selected as a preview image.
"""

import logging
import os

import gtk
from gtkmvc.view import View

from nostaples import constants

class PageView(View):
    """
    Exposes the scanned page that is currently selected as a preview 
    image.
    """
    def __init__(self, application):
        """
        Constructs the PageView, including setting up controls that could
        not be configured in Glade.
        """
        self.application = application
        page_view_glade = os.path.join(
            constants.GUI_DIRECTORY, 'page_view.glade')
        View.__init__(
            self, application.get_page_controller(), 
            page_view_glade, 'dummy_page_view_window', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)

        self['page_view_horizontal_scrollbar'].set_adjustment(
            self['page_view_image_layout'].get_hadjustment())
        self['page_view_vertical_scrollbar'].set_adjustment(
            self['page_view_image_layout'].get_vadjustment())
        
        self['page_view_image_layout'].modify_bg(
            gtk.STATE_NORMAL, 
            gtk.gdk.colormap_get_system().alloc_color(
                gtk.gdk.Color(0, 0, 0), False, True))
        
        application.get_page_controller().register_view(self)
        
        self.log.debug('Created.')
