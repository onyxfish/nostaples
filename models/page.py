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
This module holds the PageModel, which represents a single scanned page.
"""

import logging

import gtk
from gtkmvc.model import Model

class PageModel(Model):
    """
    Represents a single scanned page.
    """
    __properties__ = \
    {
        'path' : '',
        '_raw_pixbuf' : None,
        'rotation' : 0,
        'brightness' : 1.0,
        'contrast' : 1.0,
        'sharpness' : 1.0,
        'resolution' : 75,
        'pixbuf' : None,
        'thumbnail_pixbuf' : None,
    }

    # SETUP METHODS
    
    def __init__(self, path='', resolution=75):
        """
        Constructs the PageModel.
        
        TODO: @param defintions
        """
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.path = path
        self.resolution = resolution
        
        if path:
            self._raw_pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        
        self.register_observer(self)
        
        self.log.debug('Created.')
        
    # COMPUTED PROPERTIES
    
    @property
    def width(self):
        """
        Gets the width of the page, correctly adjusting if the page
        has been rotated.
        """
        if abs(self.rotation % 360) == 90 or \
           abs(self.rotation % 360) == 270:
            return self._raw_pixbuf.get_height()
        else:
            return self._raw_pixbuf.get_width()
        
    @property
    def height(self):
        """
        Gets the height of the page, correctly adjusting if the page
        has been rotated.
        """
        if abs(self.rotation % 360) == 90 or \
           abs(self.rotation % 360) == 270:
            return self._raw_pixbuf.get_width()
        else:
            return self._raw_pixbuf.get_height()
    
    # PROPERTY CALLBACKS
        
    def property_rotation_value_change(self, model, old_value, new_value):
        pass
        
    def property_brightness_value_change(self, model, old_value, new_value):
        pass
        
    def property_contrast_value_change(self, model, old_value, new_value):
        pass
        
    def property_sharpness_value_change(self, model, old_value, new_value):
        pass
    
    # UTILITY METHODS
