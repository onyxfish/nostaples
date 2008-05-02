#!/usr/env/python

# TODO - unpaper as a scan option?

# Import statements

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

# Classes

class NoStaplesApplication:
	'''NoStaples' main application class.'''

	def __init__(self):
		self.scannedPages = []	# List of Page objects
		self.nextScanFileIndex = 0
		self.previewIndex = 0
		self.previewPixbuf = None
		self.previewWidth = 0
		self.previewHeight = 0
		self.previewZoom = 1.0
		self.previewIsBestFit = True
		self.baseStatusContextId = 0
		self.previewStatusContextId = 1
		self.scanStatusContextId = 2
		
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
		
		self.previewLayout = self.gladeTree.get_widget('PreviewLayout')
		self.previewHScroll = self.gladeTree.get_widget('PreviewHScroll')
		self.previewVScroll = self.gladeTree.get_widget('PreviewVScroll')
		
		self.previewHScroll.set_adjustment(self.previewLayout.get_hadjustment())
		self.previewVScroll.set_adjustment(self.previewLayout.get_vadjustment())
		
		self.previewImageDisplay = gtk.Image()
		self.previewLayout.add(self.previewImageDisplay)
		self.previewImageDisplay.show()
		
		#self.previewImageDisplayLabel = self.gladeTree.get_widget('PreviewImageDisplayLabel')
		#self.previewWidth, self.previewHeight  = self.previewImageDisplay.size_request()
		#self.previewLayout.set_size(self.previewWidth, self.previewHeight)

		self.scanStatusBar = self.gladeTree.get_widget('ScanStatusBar')
		self.scanStatusBar.push(self.baseStatusContextId, 'Ready')

		signals = {'on_ScanWindow_destroy' : self.quit,
					'on_ScanMenuItem_activate' : self.scan_page,
					'on_SaveAsMenuItem_activate' : self.save_as,
					'on_PreferencesMenuItem_activate' : self.show_preferences,
					'on_ZoomInMenuItem_activate' : self.zoom_in,
					'on_ZoomOutMenuItem_activate' : self.zoom_out,
					'on_ZoomOneToOneMenuItem_activate' : self.zoom_one_to_one,
					'on_ZoomBestFitMenuItem_activate' : self.zoom_best_fit,
					'on_GoFirstMenuItem_activate' : self.goto_first_page,
					'on_GoPreviousMenuItem_activate' : self.goto_previous_page,
					'on_GoNextMenuItem_activate' : self.goto_next_page,
					'on_GoLastMenuItem_activate' : self.goto_last_page,
					'on_AboutMenuItem_activate' : self.show_about,
					'on_ScanButton_clicked' : self.scan_page,
					'on_SaveAsButton_clicked' : self.save_as,
					'on_ZoomInButton_clicked' : self.zoom_in,
					'on_ZoomOutButton_clicked' : self.zoom_out,
					'on_ZoomOneToOneButton_clicked' : self.zoom_one_to_one,
					'on_ZoomBestFitButton_clicked' : self.zoom_best_fit,
					'on_GoFirstButton_clicked' : self.goto_first_page,
					'on_GoPreviousButton_clicked' : self.goto_previous_page,
					'on_GoNextButton_clicked' : self.goto_next_page,
					'on_GoLastButton_clicked' : self.goto_last_page,
					'on_ScannerComboBox_changed' : self.update_scanner_options,
					'on_RefreshScannerListButton_clicked' : self.update_scanner_list,
					'on_RotateLeftButton_clicked' : self.rotate_left,
					'on_RotateRightButton_clicked' : self.rotate_right,
					'on_BrightnessScale_value_changed' : self.update_brightness,		
					'on_ContrastScale_value_changed' : self.update_contrast,		
					'on_SharpnessScale_value_changed' : self.update_sharpness,
					'on_ColorAllPagesCheck_toggled' : self.color_all_pages_toggled,
					'on_PreviewLayout_size_allocate' : self.preview_resized}
		self.gladeTree.signal_autoconnect(signals)
		
	# GUI utility functions
		
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

	def error_box(self, parent, text):
		'''Utility function to display simple error dialog.'''
		self.errorDialog.set_transient_for(parent)
		self.errorLabel.set_markup(text)
		self.errorDialog.run()
		self.errorDialog.hide()
		
	# Signal handlers
	
	def quit(self, window=None):
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
		
	def zoom_in(self, widget=None):
		'''Zooms the preview image in by 50%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom +=  0.5
		
		if self.previewZoom > 5:
			self.previewZoom = 5
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_preview_status()
		
	def zoom_out(self, widget=None):
		'''Zooms the preview image out by 50%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom -=  0.5
		
		if self.previewZoom < 0.5:
			self.previewZoom = 0.5
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_preview_status()
		
	def zoom_one_to_one(self, widget=None):
		'''Zooms the preview image to exactly 100%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom =  1.0
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_preview_status()
		
	def zoom_best_fit(self, widget=None):
		'''Zooms the preview image so that the entire image is displayed.'''
		if len(self.scannedPages) < 1:
			return
		
		width = self.previewPixbuf.get_width()
		height = self.previewPixbuf.get_height()
		
		widthRatio = float(width) / self.previewWidth
		heightRatio = float(height) / self.previewHeight
		
		if widthRatio < heightRatio:
			self.previewZoom =  1 / float(heightRatio)
		else:
			self.previewZoom =  1 / float(widthRatio)
			
		self.previewIsBestFit = True
			
		self.render_preview()
		self.update_preview_status()
		
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
			
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()
		
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
			
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()
		
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
			self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
			self.render_preview()
		
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
			self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
			self.render_preview()
		
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
			self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
			self.render_preview()
			
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
		
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()
		
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
		
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()
		
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
		
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()
		
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
		
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()

	def preview_resized(self, window, rect):
		'''Catches preview display size allocations so that the preview image can be appropriately scaled to fit the display.'''
		if rect.width == self.previewWidth and rect.height == self.previewHeight:
			return
			
		self.previewWidth = rect.width
		self.previewHeight = rect.height
		
		if len(self.scannedPages) < 1:
			return
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_preview_status()
		
	def scan_page(self, button=None):
		'''Starts the scanning thread.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		# Must always create a new thread, because they can only be started once
		self.scanningThread = ScanningThread(self)
		self.scanningThread.start()
	
	def save_as(self, widget=None):
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
		self.update_preview_status()
		
	# Functions not tied to a signal handler
	
	def update_preview_status(self):
		self.scanStatusBar.pop(self.previewStatusContextId)
		
		if len(self.scannedPages) > 0:
			self.scanStatusBar.push(self.previewStatusContextId,'Page %i of %i\t%i%%' % (self.previewIndex + 1, len(self.scannedPages), int(self.previewZoom * 100)))
		
	def render_preview(self):
		'''Render the current page to the preview display.'''
		assert len(self.scannedPages) > 0, 'Render request made when no pages have been scanned.'
		
		# Zoom if necessary
		if self.previewZoom != 1.0:
			targetWidth = int(self.previewPixbuf.get_width() * self.previewZoom)
			targetHeight = int(self.previewPixbuf.get_height() * self.previewZoom)
			
			pixbuf = self.previewPixbuf.scale_simple(targetWidth, targetHeight, gtk.gdk.INTERP_BILINEAR)
		else:
			targetWidth = self.previewPixbuf.get_width()
			targetHeight = self.previewPixbuf.get_height()
			
			pixbuf = self.previewPixbuf
		
		# Resize preview area
		self.previewLayout.set_size(targetWidth, targetHeight)
		
		# Center preview
		shiftX = int((self.previewWidth - targetWidth) / 2)
		if shiftX < 0:
			shiftX = 0
		shiftY = int((self.previewHeight - targetHeight) / 2)
		if shiftY < 0:
			shiftY = 0
		self.previewLayout.move(self.previewImageDisplay, shiftX, shiftY)
		
		# Show/hide scrollbars
		if targetWidth > self.previewWidth:
			self.previewHScroll.show()
		else:
			self.previewHScroll.hide()
			
		if targetHeight > self.previewHeight:
			self.previewVScroll.show()
		else:
			self.previewVScroll.hide()
		
		# Render updated preview
		self.previewImageDisplay.set_from_pixbuf(pixbuf)
		
class ScanningThread(threading.Thread):
	'''A Thread object for scanning documents without hanging the GUI.'''
	
	def __init__(self, app):
		self.app = app
		self.stopThreadEvent = threading.Event()
		
		threading.Thread.__init__(self)
	
	def run(self):
		'''Scans a page with "scanimage" and appends it to the end of the current document.'''
		gtk.gdk.threads_enter()
		
		self.app.scanStatusBar.push(self.app.scanStatusContextId,'Scanning...')
		
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
		
		assert os.path.exists(expectedFilename), 'Scanning completed, but output file "%s" could not be found.' % expectedFilename
		
		newPage = Page(expectedFilename)
		
		gtk.gdk.threads_enter()
		newPage.brightness = self.app.brightnessScale.get_value()
		newPage.contrast = self.app.contrastScale.get_value()
		newPage.sharpness = self.app.sharpnessScale.get_value()
			
		self.app.scannedPages.append(newPage)
		self.app.nextScanFileIndex += 1
		self.app.previewIndex = len(self.app.scannedPages) - 1
		self.app.previewPixbuf = self.app.scannedPages[self.app.previewIndex].get_pixbuf()
		
		self.app.render_preview()
		
		self.app.update_preview_status()
		self.app.scanStatusBar.pop(self.app.scanStatusContextId)	
		
		gtk.gdk.threads_leave()
		
	def stop(self):
		self.stopThreadEvent.set()
		self.app.scanStatusBar.pop(self.scanStatusContextId)
		
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
		assert os.path.exists(filename), 'Image file "%s" could not be found.' % filename
		
		self.filename = filename
		self.rotation = 0
		self.brightness = 1.0
		self.contrast = 1.0
		self.sharpness = 1.0
		
		self.rawPixbuf = gtk.gdk.pixbuf_new_from_file(self.filename)
		# TODO
		# self.thumbnail = ?

	def convert_image_to_pixbuf(self, image):
		'''Utility function to quickly convert a PIL Image to a GTK Pixbuf.
		Adapted from Comix.'''
			
		imageString = image.tostring()			
		pixbuf = gtk.gdk.pixbuf_new_from_data(imageString, gtk.gdk.COLORSPACE_RGB, False, 8, image.size[0], image.size[1], 3 * image.size[0])
		
		return pixbuf

	def convert_pixbuf_to_image(self, pixbuf):
		'''Utility function to quickly convert a GTK Pixbuf to a PIL Image.
		Adapted from Comix.'''

		dimensions = pixbuf.get_width(), pixbuf.get_height()
		stride = pixbuf.get_rowstride()
		pixels = pixbuf.get_pixels()
		image =  Image.frombuffer('RGB', dimensions, pixels, 'raw', 'RGB', stride, 1)
		
		return image
		
	def get_pixbuf(self):
		if self.brightness != 1.0 or self.contrast != 1.0 or self.sharpness != 1.0:
			image = self.convert_pixbuf_to_image(self.rawPixbuf)
			
			if self.brightness != 1.0:
				image = ImageEnhance.Brightness(image).enhance(self.brightness)
			if self.contrast != 1.0:
				image = ImageEnhance.Contrast(image).enhance(self.contrast)
			if self.sharpness != 1.0:
				image = ImageEnhance.Sharpness(image).enhance(self.sharpness)
				
			pixbuf = self.convert_image_to_pixbuf(image)
		else:
			pixbuf = self.rawPixbuf
		
		if abs(self.rotation % 360) == 90:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
		elif abs(self.rotation % 360) == 180:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
		elif abs(self.rotation % 360) == 270:
			pixbuf = pixbuf.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
			
		return pixbuf
		
# Main loop

if __name__ == '__main__':
	app = NoStaplesApplication()
	gtk.gdk.threads_enter()
	gtk.main()
	gtk.gdk.threads_leave()