#!/usr/env/python

# TODO - unpaper as a scan option?

import os
import re
from StringIO import StringIO
from subprocess import Popen, PIPE, STDOUT
import threading
import signal
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import Image, ImageEnhance
from pyPdf.pdf import *

gtk.gdk.threads_init()

class NoStaplesApplication:
	'''NoStaples' main application class.'''

	def __init__(self):
		self.scannedPages = []	# List of Page objects
		self.nextScanFileIndex = 0
		self.previewIndex = 0
		
		self.scanningThread = ScanningThread(self)
		
		self.gladefile = 'nostaples.glade'
		self.gladeTree = gtk.glade.XML(self.gladefile)
		
		self.scanWindow = self.gladeTree.get_widget('ScanWindow')
		self.scanWindow.set_property('allow-shrink', True)
		
		self.preferencesDialog = self.gladeTree.get_widget('PreferencesDialog')
		self.aboutDialog = self.gladeTree.get_widget('AboutDialog')
		self.saveDialog = self.gladeTree.get_widget('SaveDialog')
		
		self.metadataDialog = self.gladeTree.get_widget('MetadataDialog')
		
		self.errorDialog = self.gladeTree.get_widget('ErrorDialog')
		self.errorLabel = self.gladeTree.get_widget('ErrorLabel')
		
		self.scannerMenu = self.gladeTree.get_widget('ScannerMenu')
		self.scannerComboBox = self.gladeTree.get_widget('ScannerComboBox')
		self.previewModeComboBox = self.gladeTree.get_widget('PreviewModeComboBox')
		
		self.setup_combobox(self.previewModeComboBox, ['Nearest (Fastest)','Bilinear', 'Bicubic', 'Antialias (Clearest)'], 'Antialias (Clearest)')
		
		self.modesComboBox = self.gladeTree.get_widget('ModesComboBox')
		self.resolutionsComboBox = self.gladeTree.get_widget('ResolutionsComboBox')
		
		self.update_scanner_list()
		
		self.rotateLeftButton = self.gladeTree.get_widget('RotateLeftButton')
		self.rotateRightButton = self.gladeTree.get_widget('RotateRightButton')
		self.rotateAllPagesCheck = self.gladeTree.get_widget('RotateAllPagesCheck')
		
		self.brightnessScale = self.gladeTree.get_widget('BrightnessScale')
		self.contrastScale = self.gladeTree.get_widget('ContrastScale')
		self.sharpnessScale = self.gladeTree.get_widget('SharpnessScale')
		self.colorAllPagesCheck = self.gladeTree.get_widget('ColorAllPagesCheck')
		
		self.titleEntry = self.gladeTree.get_widget('TitleEntry')
		self.authorEntry = self.gladeTree.get_widget('AuthorEntry')
		self.keywordsEntry = self.gladeTree.get_widget('KeywordsEntry')
		
		self.previewImageDisplay = self.gladeTree.get_widget('PreviewImageDisplay')
		self.previewImageDisplayLabel = self.gladeTree.get_widget('PreviewImageDisplayLabel')
		self.previewWidth, self.previewHeight  = self.previewImageDisplay.size_request()
		
		signals = {'on_ScanWindow_destroy' : self.app_quit,
					'on_PreferencesMenuItem_activate' : self.show_preferences,
					'on_AboutMenuItem_activate' : self.show_about,
					'on_ScannerComboBox_changed' : self.update_scanner_options,
					'on_RefreshScannerListButton_clicked' : self.update_scanner_list,
					'on_RotateLeftButton_clicked' : self.rotate_left,
					'on_RotateRightButton_clicked' : self.rotate_right,
					'on_BrightnessScale_value_changed' : self.update_brightness,		
					'on_ContrastScale_value_changed' : self.update_contrast,		
					'on_SharpnessScale_value_changed' : self.update_sharpness,
					'on_ColorAllPagesCheck_toggled' : self.color_all_pages_toggled,
					'on_FirstPageButton_clicked' : self.goto_first_page,
					'on_PreviousPageButton_clicked' : self.goto_previous_page,
					'on_NextPageButton_clicked' : self.goto_next_page,
					'on_LastPageButton_clicked' : self.goto_last_page,
					'on_PreviewImageDisplay_size_allocate' : self.preview_resized,
					'on_ScanPageButton_clicked' : self.scan_page,
					'on_SavePDFButton_clicked' : self.finish_scanning}
		self.gladeTree.signal_autoconnect(signals)
		
	# Utility functions
		
	def setup_combobox(self, combobox, list, selection):
		'''A short-cut for setting up simple comboboxes.'''
		liststore = gtk.ListStore(gobject.TYPE_STRING)
		combobox.clear()
		combobox.set_model(liststore)
		cell = gtk.CellRendererText()
		combobox.pack_start(cell, True)
		combobox.add_attribute(cell, 'text', 0)  

		for item in list:
			liststore.append([item])
			
		try:
			index = list.index(selection)
		except ValueError:
			index = 0

		combobox.set_active(index)
		
	def read_combobox(self, combobox):
		'''A short-cut for reading from simple comboboxes.'''
		liststore = combobox.get_model()
		active = combobox.get_active()
		
		if active < 0:
			return None
			
		return liststore[active][0]
		
	def convert_image_to_pixbuf(self, image):
		'''Utility function to quickly convert a PIL Image to a GTK Pixbuf.
		Credit to Sebastian Wilhelmi, re: http://www.daa.com.au/pipermail/pygtk/2003-June/005268.html.'''
		
		file = StringIO()
		image.save(file, 'ppm')
		contents = file.getvalue()
		file.close()
		
		loader = gtk.gdk.PixbufLoader('pnm')
		loader.write(contents, len(contents))
		pixbuf = loader.get_pixbuf()
		loader.close()
		
		return pixbuf
		
	def error_box(self, parent, text):
		'''Utility function to display simple error dialog.'''
		self.errorDialog.set_transient_for(parent)
		self.errorLabel.set_markup(text)
		self.errorDialog.run()
		self.errorDialog.hide()
		
	# Signal handlers
	
	def app_quit(self, window=None):
		'''Called on ScanWindow is destroyed to cleanup threads and files.'''
		if self.scanningThread.isAlive():
			self.scanningThread.stop()
			
		for page in self.scannedPages:
			os.remove(page.filename)
		
		gtk.main_quit()
		
	def show_preferences(self, menuitem=None):
		''''Show the preferences dialog.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		self.preferencesDialog.run()
		self.preferencesDialog.hide()
		
	def show_about(self, menuitem=None):
		'''Show the about dialog.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		self.aboutDialog.run()
		self.aboutDialog.hide()

	def update_scanner_options(self, combobox=None):
		'''Extracts lists of valid scanner modes and resolutions from "scanimage".'''
		assert not self.scanningThread.isAlive(), "Scanning thread should never be running when scanner options are updated."
			
		self.selectedScanner = self.scannerComboBox.get_active()		

		updateCmd = ' '.join(['scanimage --help -d',  self.scannerDict[self.read_combobox(self.scannerComboBox)]])
		updatePipe = Popen(updateCmd, shell=True, stderr=STDOUT, stdout=PIPE)
		updatePipe.wait()
		
		output = updatePipe.stdout.read()		
		
		try:
			self.modesList = re.findall('--mode (.*) ', output)[0].split('|')
			self.resolutionsList = re.findall('--resolution (.*)dpi ', output)[0].split('|')
		except:
			print 'Failed to parse scanner options from command: "%s"' % updateCmd
			raise
		
		self.setup_combobox(self.modesComboBox, self.modesList, self.read_combobox(self.modesComboBox))		
		self.setup_combobox(self.resolutionsComboBox, self.resolutionsList, self.read_combobox(self.resolutionsComboBox))
		
	def update_scanner_list(self, button=None):
		'''Extracts a list of valid scanners from "scanimage".'''
		assert not self.scanningThread.isAlive(), "Scanning thread should never be running when scanner list is updated."
			
		updateCmd = 'scanimage -f "%d=%v %m;"'
		updatePipe = Popen(updateCmd, shell=True, stderr=STDOUT, stdout=PIPE)
		updatePipe.wait()
		
		output = updatePipe.stdout.read()
		
		self.scannerDict = {}
		scannerList = re.findall('(.*)=(.*);', output)
		
		for v, k in scannerList:
			self.scannerDict[k] = v
		
		self.setup_combobox(self.scannerComboBox, self.scannerDict.keys(), self.read_combobox(self.scannerComboBox))
		
		self.update_scanner_options()
		
	def rotate_left(self, button=None):
		'''Rotates the current page ninety degrees counter-clockwise, or all pages if the "RotateAllPagesCheck" is toggled on.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
		
		if self.rotateAllPagesCheck.get_active():
			for page in self.scannedPages:
				page.rotation += 90
		else:
			self.scannedPages[self.previewIndex].rotation += 90
			
		self.render_preview(True)
		
	def rotate_right(self, button=None):
		'''Rotates the current page ninety degrees clockwise, or all pages if the "RotateAllPagesCheck" is toggled on.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
		
		if self.rotateAllPagesCheck.get_active():
			for page in self.scannedPages:
				page.rotation -= 90
		else:
			self.scannedPages[self.previewIndex].rotation -= 90
			
		self.render_preview(True)
		
	def update_brightness(self, scale=None):
		'''Updates the brightness of the current page, or all pages if the "ColorAllPagesCheck" is toggled on.'''
		if len(self.scannedPages) < 1:
			return
		
		if self.colorAllPagesCheck.get_active():
			for page in self.scannedPages:
				page.brightness = self.brightnessScale.get_value()		
		else:
			if not self.scanningThread.isAlive():
				self.scannedPages[self.previewIndex].brightness = self.brightnessScale.get_value()
		
		if not self.scanningThread.isAlive():
			self.render_preview(False)
		
	def update_contrast(self, scale=None):		
		'''Updates the contrast of the current page, or all pages if the "ColorAllPagesCheck" is toggled on.'''	
		if len(self.scannedPages) < 1:
			return
		
		if self.colorAllPagesCheck.get_active():
			for page in self.scannedPages:
				page.contrast = self.contrastScale.get_value()		
		else:
			if not self.scanningThread.isAlive():
				self.scannedPages[self.previewIndex].contrast = self.contrastScale.get_value()
		
		if not self.scanningThread.isAlive():
			self.render_preview(False)
		
	def update_sharpness(self, scale=None):	
		'''Updates the sharpness of the current page, or all pages if the "ColorAllPagesCheck" is toggled on.'''		
		if len(self.scannedPages) < 1:
			return
		
		if self.colorAllPagesCheck.get_active():
			for page in self.scannedPages:
				page.sharpness = self.sharpnessScale.get_value()		
		else:
			if not self.scanningThread.isAlive():
				self.scannedPages[self.previewIndex].sharpness = self.sharpnessScale.get_value()
		
		if not self.scanningThread.isAlive():
			self.render_preview(False)
			
	def color_all_pages_toggled(self, toggle=None):
		'''Catches the ColorAllPagesCheck being toggled on so that all per-page settings can be immediately synchronized.'''
		if self.colorAllPagesCheck.get_active():
			for page in self.scannedPages:
				page.brightness = self.brightnessScale.get_value()
				page.contrast = self.contrastScale.get_value()
				page.sharpness = self.sharpnessScale.get_value()
		
	def goto_first_page(self, button=None):
		'''Moves to the first scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		self.previewIndex = 0
		
		self.brightnessScale.set_value(self.scannedPages[self.previewIndex].brightness)
		self.contrastScale.set_value(self.scannedPages[self.previewIndex].contrast)
		self.sharpnessScale.set_value(self.scannedPages[self.previewIndex].sharpness)
		
		self.update_preview_image()
		
	def goto_previous_page(self, button=None):
		'''Moves to the previous scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		if self.previewIndex < 1:
			return
		
		self.previewIndex -= 1
		
		self.brightnessScale.set_value(self.scannedPages[self.previewIndex].brightness)
		self.contrastScale.set_value(self.scannedPages[self.previewIndex].contrast)
		self.sharpnessScale.set_value(self.scannedPages[self.previewIndex].sharpness)
		
		self.update_preview_image()
		
	def goto_next_page(self, button=None):
		'''Moves to the next scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		if self.previewIndex >= len(self.scannedPages) - 1:
			return
		
		self.previewIndex += 1
		
		self.brightnessScale.set_value(self.scannedPages[self.previewIndex].brightness)
		self.contrastScale.set_value(self.scannedPages[self.previewIndex].contrast)
		self.sharpnessScale.set_value(self.scannedPages[self.previewIndex].sharpness)
		
		self.update_preview_image()
		
	def goto_last_page(self, button=None):
		'''Moves to the last scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		self.previewIndex = len(self.scannedPages) - 1
		
		self.brightnessScale.set_value(self.scannedPages[self.previewIndex].brightness)
		self.contrastScale.set_value(self.scannedPages[self.previewIndex].contrast)
		self.sharpnessScale.set_value(self.scannedPages[self.previewIndex].sharpness)
		
		self.update_preview_image()

	def preview_resized(self, window, rect):
		'''Catches preview display size allocations so that the preview image can be appropriately scaled to fit the display.'''
		# DO NOT DO THIS (or first page scanned will not be rendered at correct size)
		#if len(self.scannedPages) < 1:
		#	return
			
		if rect.width == self.previewWidth and rect.height == self.previewHeight:
			return
		
		self.previewWidth = rect.width
		self.previewHeight = rect.height
		self.render_preview(True)
		
	def scan_page(self, button=None):
		'''Starts the scanning thread.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		# Must always create a new thread, because they can only be started once
		self.scanningThread = ScanningThread(self)
		self.scanningThread.start()
	
	def finish_scanning(self, button=None):
		'''Gets PDF Metadata from the user, prompts for a filename, and saves the document to PDF.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			self.error_box(self.scanWindow, 'No pages have been scanned.')
			return
			
		title = ''
		author = ''
		keywords =''
		
		while title == '':
			response = self.metadataDialog.run()
		
			if response != 1:
				self.metadataDialog.hide()
				return
			
			title = unicode(self.titleEntry.get_text())
			author = unicode(self.authorEntry.get_text())
			keywords = unicode(self.keywordsEntry.get_text())
		
			if title == '':
				self.error_box(self.scanWindow, 'You must provide a title for this document.')
			
		self.metadataDialog.hide()
		
		filter = gtk.FileFilter()
		filter.set_name('PDF Files')
		filter.add_pattern('*.pdf')
		self.saveDialog.add_filter(filter)
		
		filename = ''.join([title.replace(' ', '-').lower(), '.pdf'])
		self.saveDialog.set_current_name(filename)
		
		response = self.saveDialog.run()
		self.saveDialog.hide()
		
		if response != 1:
			return
			
		filename = self.saveDialog.get_filename()
		
		output = NoStaplesPdfFileWriter(title, author, keywords)
			
		for page in self.scannedPages:
			tempImage = Image.open(page.filename)
			pdfFilename = ''.join([page.filename[:-4], '.pdf'])
			
			rotatedImage = tempImage.rotate(page.rotation)
			brightenedImage = ImageEnhance.Brightness(rotatedImage).enhance(page.brightness)
			contrastedImage = ImageEnhance.Contrast(brightenedImage).enhance(page.contrast)
			sharpenedImage = ImageEnhance.Sharpness(contrastedImage).enhance(page.sharpness)
			
			sharpenedImage.save(pdfFilename)
			
			# check file exists?
			
			input = PdfFileReader(file(pdfFilename, 'rb'))
			output.addPage(input.getPage(0))
			
			os.remove(pdfFilename)
			
		output.write(file(filename, 'w'))
		
		for page in self.scannedPages:
			os.remove(page.filename)
		
		self.scannedPages = []
		self.nextScanFileIndex = 1
		self.previewIndex = 0
		self.previewImageDisplayLabel.set_markup('<b>Preview</b>')
		self.previewImageDisplay.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
		
	# Update functions not tied to a signal handler

	def update_preview_image(self):
		'''Loads a new image for preview.'''
		if len(self.scannedPages) < 1:
			return
			
		filename = self.scannedPages[self.previewIndex].filename
		
		assert os.path.exists(filename), 'Image file "%s" could not be found.' % filename
		
		self.fileImage = Image.open(filename)
		self.previewImageDisplayLabel.set_markup('<b>Previewing Page %i of %i</b>' % (self.previewIndex + 1, len(self.scannedPages)))
		self.render_preview(True)
				
	def render_preview(self, updateSizeAndRotation):
		'''Starts the rendering thread.'''
		if len(self.scannedPages) < 1:
			return
			
		# Must always create a new thread, because they can only be started once
		renderingThread = RenderingThread(self, updateSizeAndRotation)			
		renderingThread.start()
		
class ScanningThread(threading.Thread):
	'''A Thread object for scanning documents without hanging the GUI.'''
	
	def __init__(self, app):
		self.app = app
		self.stopThreadEvent = threading.Event()
		
		threading.Thread.__init__(self)
	
	def run(self):
		'''Scans a page with "scanimage" and appends it to the end of the current document.'''
		gtk.gdk.threads_enter()
		self.app.previewImageDisplay.set_from_file('loading.gif')
		self.app.previewImageDisplayLabel.set_markup('<b>Scanning Page %i of %i</b>' % (len(self.app.scannedPages) + 1, len(self.app.scannedPages) + 1))
		
		if not self.app.colorAllPagesCheck.get_active():
			self.app.brightnessScale.set_value(1.0)
			self.app.contrastScale.set_value(1.0)
			self.app.sharpnessScale.set_value(1.0)
		gtk.gdk.threads_leave()
		
		scanProgram = 'scanimage --format=pnm'
		modeFlag = ' '.join(['--mode', self.app.read_combobox(self.app.modesComboBox)])
		resolutionFlag = ' '.join(['--resolution', self.app.read_combobox(self.app.resolutionsComboBox)])
		scannerFlag = ' '.join(['-d', self.app.scannerDict[self.app.read_combobox(self.app.scannerComboBox)]])
		outputFile = '>scan%i.pnm' % self.app.nextScanFileIndex
		scanCmd = ' '.join([scanProgram, modeFlag, resolutionFlag, scannerFlag, outputFile])
		
		print 'Scanning with command: "%s"' % scanCmd
		scanPipe = Popen(scanCmd, shell=True, stderr=STDOUT, stdout=PIPE)
		
		while scanPipe.poll() == None:
			if self.stopThreadEvent.isSet():
				os.kill(scanPipe.pid, signal.SIGTERM)
				print 'Scan terminated'
				return
				
		print 'Scan complete'
		
		expectedFilename = ''.join(['scan', str(self.app.nextScanFileIndex), '.pnm'])
		
		assert os.exists(expectedFilename), 'Scanning completed, but output file "%s" could not be found.' % expectedFilename
		
		newPage = Page(expectedFilename)
		
		gtk.gdk.threads_enter()
		newPage.brightness = self.app.brightnessScale.get_value()
		newPage.contrast = self.app.contrastScale.get_value()
		newPage.sharpness = self.app.sharpnessScale.get_value()
			
		self.app.scannedPages.append(newPage)
		self.app.nextScanFileIndex += 1
		self.app.previewIndex = len(self.app.scannedPages) - 1
		
		self.app.update_preview_image()
		gtk.gdk.threads_leave()
		
	def stop(self):
		self.stopThreadEvent.set()
		
class RenderingThread(threading.Thread):
	'''A Thread object for updating the preview image without hanging the GUI.'''
	
	def __init__(self, app, updateSizeAndRotation):
		self.app = app
		self.updateSizeAndRotation = updateSizeAndRotation
		
		threading.Thread.__init__(self)
	
	def run(self):
		'''Renders the current preview image with selected transformations.'''
		gtk.gdk.threads_enter()
		page = self.app.scannedPages[self.app.previewIndex]
		
		if self.updateSizeAndRotation:			
			if page.rotation % 360 != 0:
				rotatedImage = self.app.fileImage.rotate(page.rotation)
			else:
				rotatedImage = self.app.fileImage
				
			# Credit to the Mirage Image Viewer app for resizing code
			widthRatio = float(rotatedImage.size[0]) / self.app.previewWidth
			heightRatio = float(rotatedImage.size[1]) / self.app.previewHeight
			
			if widthRatio < heightRatio:
				zoom =  1 / float(heightRatio)
			else:
				zoom =  1 / float(widthRatio)
				
			targetWidth = int(rotatedImage.size[0] * zoom)
			targetHeight = int(rotatedImage.size[1] * zoom)
			
			mode = self.app.read_combobox(self.app.previewModeComboBox)
			
			if mode == 'Nearest (Fastest)':
				mode = Image.NEAREST
			elif mode == 'Bilinear':
				mode = Image.BILINEAR
			elif mode == 'Bicubic':
				mode = Image.BICUBIC
			elif mode == 'Antialias (Clearest)':
				mode = Image.ANTIALIAS
			
			self.app.resizedImage = rotatedImage.resize((targetWidth, targetHeight), mode)
		
		previewImage = self.app.resizedImage
		
		if page.brightness != 1.0:
			previewImage = ImageEnhance.Brightness(previewImage).enhance(page.brightness)
		if page.contrast != 1.0:
			previewImage = ImageEnhance.Contrast(previewImage).enhance(page.contrast)
		if page.sharpness != 1.0:
			previewImage = ImageEnhance.Sharpness(previewImage).enhance(page.sharpness)
		
		self.app.previewImageDisplay.set_from_pixbuf(self.app.convert_image_to_pixbuf(previewImage))
		gtk.gdk.threads_leave()
		
class NoStaplesPdfFileWriter(PdfFileWriter):
	'''A subclass of a PyPdf PdfFileWriter that adds support for custom meta-data.'''
	
	def __init__(self, title, author, keywords):
		self._header = '%PDF-1.3'
		self._objects = []
		
		pages = DictionaryObject()
		pages.update({NameObject('/Type'): NameObject('/Pages'),
					NameObject('/Count'): NumberObject(0),
					NameObject('/Kids'): ArrayObject()})
		self._pages = self._addObject(pages)
		
		info = DictionaryObject()
		info.update({NameObject('/Producer'): createStringObject(u'NoStaples w/ Python PDF Library'),
					NameObject('/Title'): createStringObject(title),
					NameObject('/Author'): createStringObject(author),
					NameObject('/Keywords'): createStringObject(keywords)})
		self._info = self._addObject(info)
	
		root = DictionaryObject()
		root.update({NameObject('/Type'): NameObject('/Catalog'),
					NameObject('/Pages'): self._pages})
		self._root = self._addObject(root)

class Page:
	'''A simple utility class for holding per-page page properties.'''
	
	def __init__(self, filename):
		self.filename = filename
		self.rotation = 0
		self.brightness = 1.0
		self.contrast = 1.0
		self.sharpness = 1.0

if __name__ == '__main__':
	app = NoStaplesApplication()
	gtk.gdk.threads_enter()
	gtk.main()
	gtk.gdk.threads_leave()