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
import Image, ImageEnhance

from nostaples import constants
from nostaples.utils.graphics import *

class PageModel(Model):
    """
    Represents a single scanned page.
    """
    __properties__ = \
    {
        '_raw_pil_image' : None,
        
        'rotation' : 0,
        'brightness' : 1.0,
        'contrast' : 1.0,
        'sharpness' : 1.0,
        'resolution' : 75,
        
        'pixbuf' : None,
        'thumbnail_pixbuf': None,
    }

    # SETUP METHODS
    
    def __init__(self, application, pil_image=None, resolution=75):
        """
        Constructs the PageModel.
        
        @type pil_image: a PIL image
        @param pil_image: The image data for this page.
        @type resolution: int
        @param resolution: The dpi that the page was
                           scanned at.
        """
        self.application = application
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.resolution = resolution
        
        if pil_image:
            self._raw_pil_image = pil_image
            self._update_pixbuf()
            self._update_thumbnail_pixbuf()
        
        self.register_observer(self)
        
        # TODO: Wtf am I doing here, solves a bug, but why?
        self.accepts_spurious_change = lambda : True
        
        self.log.debug('Created.')
        
    # COMPUTED PROPERTIES
    
    @property
    def width(self):
        """
        Gets the width of the page after transformations have been
        applied.
        """
        return self.pixbuf.get_width()
        
    @property
    def height(self):
        """
        Gets the height of the page after transformations have been
        applied.
        """
        return self.pixbuf.get_height()
    
    # PROPERTY CALLBACKS
        
    def property_rotation_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
        
    def property_brightness_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
        
    def property_contrast_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
        
    def property_sharpness_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
    
    # PUBLIC METHODS
    
    def rotate_counter_clockwise(self):
        """
        Rotate this page ninety degrees counter-clockwise.
        """
        self.rotation += 90
    
    def rotate_clockwise(self):
        """
        Rotate this page ninety degrees clockwise.
        """
        self.rotation -= 90
        
    def set_adjustments(self, brightness, contrast, sharpness):
        """
        Sets all three adjustment values in one method without
        triggering each property callback.  This prevents
        the pixbuf and thumbnail from being update multiple
        times.
        """
        if (self.__properties__['brightness'] == brightness and
            self.__properties__['contrast'] == contrast and
            self.__properties__['sharpness'] == sharpness):
            return
        
        self.__properties__['brightness'] = brightness
        self.__properties__['contrast'] = contrast
        self.__properties__['sharpness'] = sharpness  
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()      
    
    # PRIVATE METHODS
    
    def _update_pixbuf(self):
        """
        Creates a full-size pixbuf of the scanned image with all 
        transformations applied.
        """   
        image = self._raw_pil_image  
        
        if self.brightness != 1.0:
            image = ImageEnhance.Brightness(image).enhance(
                self.brightness)
        if self.contrast != 1.0:
            image = ImageEnhance.Contrast(image).enhance(
                self.contrast)
        if self.sharpness != 1.0:
            image = ImageEnhance.Sharpness(image).enhance(
                self.sharpness)
            
        if abs(self.rotation % 360) == 90:
            image = image.transpose(Image.ROTATE_90)
        elif abs(self.rotation % 360) == 180:
            image = image.transpose(Image.ROTATE_180)
        elif abs(self.rotation % 360) == 270:
            image = image.transpose(Image.ROTATE_270)
            
        self.pixbuf = convert_pil_image_to_pixbuf(image)
        
    def _update_thumbnail_pixbuf(self):
        """
        Creates a thumbnail image with all transformations applied.
        """
        preferences_model = self.application.get_preferences_model()
            
        image = self._raw_pil_image
            
        if self.brightness != 1.0:
            image = ImageEnhance.Brightness(image).enhance(
                self.brightness)
        if self.contrast != 1.0:
            image = ImageEnhance.Contrast(image).enhance(
                self.contrast)
        if self.sharpness != 1.0:
            image = ImageEnhance.Sharpness(image).enhance(
                self.sharpness)
        
        if abs(self.rotation % 360) == 90:
            image = image.transpose(Image.ROTATE_90)
        elif abs(self.rotation % 360) == 180:
            image = image.transpose(Image.ROTATE_180)
        elif abs(self.rotation % 360) == 270:
            image = image.transpose(Image.ROTATE_270)
            
        width, height = image.size
        
        thumbnail_size = preferences_model.thumbnail_size
        
        width_ratio = float(width) / thumbnail_size
        height_ratio = float(height) / thumbnail_size
        
        if width_ratio < height_ratio:
            zoom =  1 / float(height_ratio)
        else:
            zoom =  1 / float(width_ratio)
            
        target_width = int(width * zoom)
        target_height = int(height * zoom)
        
        image = image.resize(
            (target_width, target_height), 
            Image.ANTIALIAS)
        
        self.thumbnail_pixbuf = convert_pil_image_to_pixbuf(image)