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
This module holds the ScannerModel, which represents a connected
scanning device.
"""

import logging

import gtk
from gtkmvc.model import Model

class ScannerModel(Model):
    """
    Represents a single scanned page.
    """
    __properties__ = \
    {
        'display_name' : '',
        'sane_name' : '',
        'valid_modes' : [],
        'valid_resolutions' : [],
        'active_mode' : None,
        'active_resolution' : None,
        'is_device_in_use' : False,
    }

    # SETUP METHODS
    
    def __init__(self, display_name, sane_name):
        """
        Constructs the ScannerModel.
        
        TODO: @param defintions
        """
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.display_name = display_name
        self.sane_name = sane_name
        
        self.log.debug('Created.')
    
    # PUBLIC METHODS
    
    # PRIVATE METHODS