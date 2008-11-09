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
This module holds the ScannerView which exposes the options for the
currently selected scanner.
"""

import logging

import gtk
from gtkmvc.view import View

import constants

class ScannerView(View):
    """
    TODO
    """
    def __init__(self, controller):
        """
        Constructs the ScannerView, including setting up controls that could
        not be configured in Glade.
        """
        View.__init__(
            self, controller, constants.GLADE_CONFIG, 
            'dummy_scanner_view_window', None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        controller.register_view(self)
        
        self.log.debug('Created.')
