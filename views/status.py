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
This module holds the StatusView which exposes the application
statusbar.
"""

import logging
import os

import gtk
from gtkmvc.view import View

import constants

class StatusView(View):
    """
    Exposes the application statusbar.
    """

    def __init__(self, application):
        """
        Constructs the StatusView.
        """
        self.application = application
        status_view_glade = os.path.join(
            constants.GUI_DIRECTORY, 'status_view.glade')
        View.__init__(
            self, application.get_status_controller(), 
            status_view_glade, 'dummy_status_view_window', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        application.get_status_controller().register_view(self)
        
        self.log.debug('Created.')