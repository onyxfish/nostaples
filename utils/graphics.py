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
This module holds utility functions for converting between
GTK and PIL graphics formats.
"""

import gtk
import Image

# TODO: move these utility functions into own module? 
def convert_pil_image_to_pixbuf(image):
    """
    Utility function to quickly convert a PIL Image to a GTK Pixbuf.
    Adapted from Comix by Pontus Ekberg. (http://comix.sourceforge.net/)
    """
    image_string = image.tostring()            
    pixbuf = gtk.gdk.pixbuf_new_from_data(
        image_string, gtk.gdk.COLORSPACE_RGB, 
        False, 8, image.size[0], image.size[1], 3 * image.size[0])
    
    return pixbuf

def convert_pixbuf_to_pil_image(pixbuf):
    """
    Utility function to quickly convert a GTK Pixbuf to a PIL Image.
    Adapted from Comix by Pontus Ekberg. (http://comix.sourceforge.net/)
    """
    dimensions = pixbuf.get_width(), pixbuf.get_height()
    stride = pixbuf.get_rowstride()
    pixels = pixbuf.get_pixels()
    image =  Image.frombuffer(
        'RGB', dimensions, pixels, 'raw', 'RGB', stride, 1)
    
    return image