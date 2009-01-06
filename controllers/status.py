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
This module holds the L{StatusController}, which manages interaction 
between the L{StatusModel} and L{StatusView}.
"""

import logging

import gtk
from gtkmvc.controller import Controller

class StatusController(Controller):
    """
    Manages interaction between the L{StatusModel} and
    L{StatusView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the StatusController.
        """
        self.application = application
        Controller.__init__(self, application.get_status_model())

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def get_context_id(self, description):
        status_view = self.application.get_status_view()
        return status_view['statusbar'].get_context_id(description)
        
    def push(self, context_id, message):
        status_view = self.application.get_status_view()
        return status_view['statusbar'].push(context_id, message)
    
    def pop(self, context_id):
        status_view = self.application.get_status_view()
        status_view['statusbar'].pop(context_id)
    
    def remove(self, message_id):
        status_view = self.application.get_status_view()
        status_view['statusbar'].remove(message_id)