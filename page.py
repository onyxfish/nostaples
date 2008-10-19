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
The class in this module represents a single scanned page.  It has methods
to handle transforming and converting the page as necessary for display.
'''

import os
import Image, ImageEnhance
import gtk

class Page:
    '''
    A simple convience class for holding per-scanned-page properties and 
    abstracting away image transformations.
    '''
    
    def __init__(self, path, resolution):
        '''
        Constructs a Page object and pulls a local copy of the image from 
        the scan file.
        '''
        assert os.path.exists(path), \
            'Image file "%s" could not be found.' % path
        
        self.path = path
        self.rotation = 0
        self.brightness = 1.0
        self.contrast = 1.0
        self.sharpness = 1.0
        self.resolution = resolution
        
        self._raw_pixbuf = gtk.gdk.pixbuf_new_from_file(self.path)
        
    @property
    def width(self):
        '''Gets the width of the page.'''
        return self._raw_pixbuf.get_width()
        
    @property
    def height(self):
        '''Gets the height of the page.'''
        return self._raw_pixbuf.get_height() 
                
    @property
    def pixbuf(self):
        '''
        Generates a GTK Pixbuf that has had rotation and color adjustments 
        applied to it (i.e. a working copy).
        '''
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
                
            pixbuf = self.__convert_pil_image_to_pixbuf(image)
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
            
        return pixbuf
                
    @property
    def pil_image(self):
        '''
        Returns a PIL version of the transformed pixbuf for this page.
        
        This could be sped up by bypassing the conversion to and from
        a PIL image in L{pixbuf}, but this is not a speed intensive 
        routine and requires less maintenance this way.
        '''
        return convert_pixbuf_to_pil_image(self.pixbuf)
        
    def get_thumbnail_pixbuf(self, size):
        '''
        Generates a GTK Pixbuf that has had rotation and color adjustments 
        applied to it and has been scaled down to fit the thumbnail pager.
        '''
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
        
        width_ratio = float(width) / size
        height_ratio = float(height) / size
        
        if width_ratio < height_ratio:
            zoom =  1 / float(height_ratio)
        else:
            zoom =  1 / float(width_ratio)
            
        target_width = int(pixbuf.get_width() * zoom)
        target_height = int(pixbuf.get_height() * zoom)
            
        pixbuf = pixbuf.scale_simple(
            target_width, target_height, gtk.gdk.INTERP_BILINEAR)
        
        return pixbuf
    
    def save(self, file_path):
        '''Saves the transformed image to a file.'''
        self.pil_image.save(file_path)

# Utility functions

def convert_pil_image_to_pixbuf(image):
    '''
    Utility function to quickly convert a PIL Image to a GTK Pixbuf.
    Adapted from Comix by Pontus Ekberg. (http://comix.sourceforge.net/)
    '''
    image_string = image.tostring()            
    pixbuf = gtk.gdk.pixbuf_new_from_data(
        image_string, gtk.gdk.COLORSPACE_RGB, 
        False, 8, image.size[0], image.size[1], 3 * image.size[0])
    
    return pixbuf

def convert_pixbuf_to_pil_image(pixbuf):
    '''
    Utility function to quickly convert a GTK Pixbuf to a PIL Image.
    Adapted from Comix by Pontus Ekberg. (http://comix.sourceforge.net/)
    '''
    dimensions = pixbuf.get_width(), pixbuf.get_height()
    stride = pixbuf.get_rowstride()
    pixels = pixbuf.get_pixels()
    image =  Image.frombuffer(
        'RGB', dimensions, pixels, 'raw', 'RGB', stride, 1)
    
    return image