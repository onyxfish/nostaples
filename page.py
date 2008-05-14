import os
import Image, ImageEnhance
import gtk

class Page:
	'''A simple utility class for holding per-scanned-page properties and abstracting away behind-the-scenes image manipulations.'''
	
	def __init__(self, filename):
		'''Constructs a Page object and pulls a local copy of the image from the scan file.'''
		assert os.path.exists(filename), 'Image file "%s" could not be found.' % filename
		
		self.filename = filename
		self.rotation = 0
		self.brightness = 1.0
		self.contrast = 1.0
		self.sharpness = 1.0
		
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
		
	def get_transformed_pixbuf(self):
		'''Generates a GTK Pixbuf that has had rotation and color adjustments applied to it (i.e. a working copy).'''
		if self.brightness != 1.0 or self.contrast != 1.0 or self.sharpness != 1.0:
			image = self.__convert_pixbuf_to_image(self.rawPixbuf)
			
			if self.brightness != 1.0:
				image = ImageEnhance.Brightness(image).enhance(self.brightness)
			if self.contrast != 1.0:
				image = ImageEnhance.Contrast(image).enhance(self.contrast)
			if self.sharpness != 1.0:
				image = ImageEnhance.Sharpness(image).enhance(self.sharpness)
				
			pixbuf =self.__convert_image_to_pixbuf(image)
		else:
			pixbuf = self.rawPixbuf
		
		if abs(self.rotation % 360) == 90:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
		elif abs(self.rotation % 360) == 180:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
		elif abs(self.rotation % 360) == 270:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
			
		return pixbuf
		
	def get_thumbnail_pixbuf(self, size):
		'''Generates a GTK Pixbuf that hashad rotation and color adjustments applied to it and has been scaled down to fit the thumbnail pager.'''
		if self.brightness != 1.0 or self.contrast != 1.0 or self.sharpness != 1.0:
			image =self.__convert_pixbuf_to_image(self.rawPixbuf)
			
			if self.brightness != 1.0:
				image = ImageEnhance.Brightness(image).enhance(self.brightness)
			if self.contrast != 1.0:
				image = ImageEnhance.Contrast(image).enhance(self.contrast)
			if self.sharpness != 1.0:
				image = ImageEnhance.Sharpness(image).enhance(self.sharpness)
				
			pixbuf = self.__convert_image_to_pixbuf(image)
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