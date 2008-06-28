#!/usr/env/python

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

import os
import Image, ImageEnhance
import gtk

class Page:
	'''A simple convience class for holding per-scanned-page properties and abstracting away image transformations.'''
	
	def __init__(self, filename, dpi):
		'''Constructs a Page object and pulls a local copy of the image from the scan file.'''
		assert os.path.exists(filename), 'Image file "%s" could not be found.' % filename
		
		self.filename = filename
		self.rotation = 0
		self.brightness = 1.0
		self.contrast = 1.0
		self.sharpness = 1.0
		self.dpi = dpi
		
		self.rawPixbuf = gtk.gdk.pixbuf_new_from_file(self.filename)
		
	def __convert_pil_image_to_pixbuf(self, image):
		'''Utility function to quickly convert a PIL Image to a GTK Pixbuf.
		Adapted from Comix.'''
			
		imageString = image.tostring()			
		pixbuf = gtk.gdk.pixbuf_new_from_data(imageString, gtk.gdk.COLORSPACE_RGB, False, 8, image.size[0], image.size[1], 3 * image.size[0])
		
		return pixbuf

	def __convert_pixbuf_to_pil_image(self, pixbuf):
		'''Utility function to quickly convert a GTK Pixbuf to a PIL Image.
		Adapted from Comix.'''

		dimensions = pixbuf.get_width(), pixbuf.get_height()
		stride = pixbuf.get_rowstride()
		pixels = pixbuf.get_pixels()
		image =  Image.frombuffer('RGB', dimensions, pixels, 'raw', 'RGB', stride, 1)
		
		return image
		
	def get_raw_pixbuf(self):
		'''Returns an unmodified pixbuf for this page.'''
		return self.rawPixbuf
		
	def get_raw_pil_image(self):
		'''Returns a PIL version of the unmodified pixbuf for this page.'''
		return self.__convert_pixbuf_to_pil_image(self.rawPixbuf)
		
	def get_transformed_pixbuf(self):
		'''Generates a GTK Pixbuf that has had rotation and color adjustments applied to it (i.e. a working copy).'''
		if self.brightness != 1.0 or self.contrast != 1.0 or self.sharpness != 1.0:
			image = self.__convert_pixbuf_to_pil_image(self.rawPixbuf)
			
			if self.brightness != 1.0:
				image = ImageEnhance.Brightness(image).enhance(self.brightness)
			if self.contrast != 1.0:
				image = ImageEnhance.Contrast(image).enhance(self.contrast)
			if self.sharpness != 1.0:
				image = ImageEnhance.Sharpness(image).enhance(self.sharpness)
				
			pixbuf =self.__convert_pil_image_to_pixbuf(image)
		else:
			pixbuf = self.rawPixbuf
		
		if abs(self.rotation % 360) == 90:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
		elif abs(self.rotation % 360) == 180:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
		elif abs(self.rotation % 360) == 270:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
			
		return pixbuf
		
	def get_transformed_pil_image(self):
		'''Returns a PIL version of the transformed pixbuf for this page.'''
		# TODO - speed this up by bypassing all the conversion in get_transformed_pixbuf.
		return self.__convert_pixbuf_to_pil_image(self.get_transformed_pixbuf())
		
	def get_thumbnail_pixbuf(self, size):
		'''Generates a GTK Pixbuf that hashad rotation and color adjustments applied to it and has been scaled down to fit the thumbnail pager.'''
		if self.brightness != 1.0 or self.contrast != 1.0 or self.sharpness != 1.0:
			image =self.__convert_pixbuf_to_pil_image(self.rawPixbuf)
			
			if self.brightness != 1.0:
				image = ImageEnhance.Brightness(image).enhance(self.brightness)
			if self.contrast != 1.0:
				image = ImageEnhance.Contrast(image).enhance(self.contrast)
			if self.sharpness != 1.0:
				image = ImageEnhance.Sharpness(image).enhance(self.sharpness)
				
			pixbuf = self.__convert_pil_image_to_pixbuf(image)
		else:
			pixbuf = self.rawPixbuf
		
		if abs(self.rotation % 360) == 90:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
		elif abs(self.rotation % 360) == 180:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
		elif abs(self.rotation % 360) == 270:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
			
		width = pixbuf.get_width()
		height = pixbuf.get_height()
		
		widthRatio = float(width) / size
		heightRatio = float(height) / size
		
		if widthRatio < heightRatio:
			zoom =  1 / float(heightRatio)
		else:
			zoom =  1 / float(widthRatio)
			
		targetWidth = int(pixbuf.get_width() * zoom)
		targetHeight = int(pixbuf.get_height() * zoom)
			
		pixbuf = pixbuf.scale_simple(targetWidth, targetHeight, gtk.gdk.INTERP_BILINEAR)
		
		return pixbuf
		
	def get_thumbnail_pil_image(self, size):
		'''Returns a PIL version of the thumbnail pixbuf for this page.'''
		return self.__convert_pixbuf_to_pil_image(self.get_thumbnail_pixbuf(size))