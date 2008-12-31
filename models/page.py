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

from utils.graphics import *

# TODO: temp
THUMBNAIL_SIZE = 128

class PageModel(Model):
    """
    Represents a single scanned page.
    """
    __properties__ = \
    {
        'path' : None,
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
    
    def __init__(self, path=None, resolution=75):
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
    
    @property
    def pil_image(self):
        """
        Returns a PIL version of the transformed pixbuf for this page.
        
        This could be sped up by bypassing the conversion to and from
        a PIL image in L{pixbuf}, but this is not a speed intensive 
        routine and requires less maintenance this way.
        """
        return convert_pixbuf_to_pil_image(self.pixbuf)
    
    # PROPERTY CALLBACKS
        
    def property_rotation_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
        
    def property_brightness_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        print 1
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
        
    def property_contrast_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        print 2
        self._update_pixbuf()
        self._update_thumbnail_pixbuf()
        
    def property_sharpness_value_change(self, model, old_value, new_value):
        """Updates the full and thumbnail pixbufs."""
        print 3
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
        if self.brightness != 1.0 or \
           self.contrast != 1.0 or \
           self.sharpness != 1.0:
            image = convert_pixbuf_to_pil_image(self._raw_pixbuf)
            
            if self.brightness != 1.0:
                image = ImageEnhance.Brightness(image).enhance(
                    self.brightness)
            if self.contrast != 1.0:
                image = ImageEnhance.Contrast(image).enhance(
                    self.contrast)
            if self.sharpness != 1.0:
                image = ImageEnhance.Sharpness(image).enhance(
                    self.sharpness)
                
            pixbuf = convert_pil_image_to_pixbuf(image)
        else:
            pixbuf = self._raw_pixbuf
        
        if abs(self.rotation % 360) == 90:
            pixbuf = pixbuf.rotate_simple(
                gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
        elif abs(self.rotation % 360) == 180:
            pixbuf = pixbuf.rotate_simple(
                gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
        elif abs(self.rotation % 360) == 270:
            pixbuf = pixbuf.rotate_simple(
                gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
            
        self.pixbuf = pixbuf
        
    def _update_thumbnail_pixbuf(self):
        """
        Creates a thumbnail pixbuf with all transformations applied.
        """
        if self.brightness != 1.0 or \
           self.contrast != 1.0 or \
           self.sharpness != 1.0:
            image = convert_pixbuf_to_pil_image(self._raw_pixbuf)
            
            if self.brightness != 1.0:
                image = ImageEnhance.Brightness(image).enhance(
                    self.brightness)
            if self.contrast != 1.0:
                image = ImageEnhance.Contrast(image).enhance(
                    self.contrast)
            if self.sharpness != 1.0:
                image = ImageEnhance.Sharpness(image).enhance(
                    self.sharpness)
                
            pixbuf = convert_pil_image_to_pixbuf(image)
        else:
            pixbuf = self._raw_pixbuf
        
        if abs(self.rotation % 360) == 90:
            pixbuf = pixbuf.rotate_simple(
                gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
        elif abs(self.rotation % 360) == 180:
            pixbuf = pixbuf.rotate_simple(
                gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
        elif abs(self.rotation % 360) == 270:
            pixbuf = pixbuf.rotate_simple(
                gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
            
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        
        width_ratio = float(width) / THUMBNAIL_SIZE
        height_ratio = float(height) / THUMBNAIL_SIZE
        
        if width_ratio < height_ratio:
            zoom =  1 / float(height_ratio)
        else:
            zoom =  1 / float(width_ratio)
            
        target_width = int(pixbuf.get_width() * zoom)
        target_height = int(pixbuf.get_height() * zoom)
            
        self.thumbnail_pixbuf = pixbuf.scale_simple(
            target_width, target_height, gtk.gdk.INTERP_BILINEAR)