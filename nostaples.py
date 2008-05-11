#!/usr/env/python

# TODO - unpaper as a scan option?

# Import statements

from types import IntType, StringType, FloatType, BooleanType
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
import gconf
import Image, ImageEnhance
from pyPdf.pdf import *

# Globals
DEFAULT_THUMBNAIL_SIZE = 128

gtk.gdk.threads_init()

# Classes

class NoStaples:
	'''NoStaples' main application class.'''

	def __init__(self):
		self.scannerDict = {}	# Keys are human readable scanner descriptions, Values are sane-backend descriptors
		self.activeScanner = None
		self.scanMode = None
		self.scanResolution = None
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
		self.thumbnailSelection = None
		self.insertIsNotDrag = False
		
		self.gconfClient = gconf.client_get_default()
		self.thumbnailSize = self.get_gconf_setting('/apps/nostaples/thumbnail_size', DEFAULT_THUMBNAIL_SIZE)
		
		self.activeScanner = self.get_gconf_setting('/apps/nostaples/active_scanner', '')
		self.scanMode = self.get_gconf_setting('/apps/nostaples/scan_mode', 'Color')
		self.scanResolution = self.get_gconf_setting('/apps/nostaples/scan_resolution', 75)
		
		self.scanningThread = ScanningThread(self)
		
		self.gladefile = 'nostaples.glade'
		self.gladeTree = gtk.glade.XML(self.gladefile)
		
		self.scanWindow = self.gladeTree.get_widget('ScanWindow')
		self.scanWindow.set_property('allow-shrink', True)
		
		self.adjustColorsWindow = self.gladeTree.get_widget('AdjustColorsWindow')
		
		self.preferencesDialog = self.gladeTree.get_widget('PreferencesDialog')
		self.aboutDialog = self.gladeTree.get_widget('AboutDialog')
		self.saveDialog = self.gladeTree.get_widget('SaveDialog')
		self.metadataDialog = self.gladeTree.get_widget('MetadataDialog')
		
		self.errorDialog = self.gladeTree.get_widget('ErrorDialog')
		self.errorLabel = self.gladeTree.get_widget('ErrorLabel')
		
		self.previewModeComboBox = self.gladeTree.get_widget('PreviewModeComboBox')
		self.setup_combobox(self.previewModeComboBox, ['Nearest (Fastest)','Bilinear', 'Bicubic', 'Antialias (Clearest)'], 'Antialias (Clearest)')
		
		self.scannerSubMenu = self.gladeTree.get_widget('ScannerSubMenu')
		self.scanModeSubMenu = self.gladeTree.get_widget('ScanModeSubMenu')
		self.scanResolutionSubMenu = self.gladeTree.get_widget('ScanResolutionSubMenu')
		
		self.update_scanner_list()
		
		self.toolbar = self.gladeTree.get_widget('MainToolbar')
		
		self.rotateAllPagesMenuItem = self.gladeTree.get_widget('RotateAllPagesMenuItem')
		self.adjustColorsMenuItem = self.gladeTree.get_widget('AdjustColorsMenuItem')
		
		self.brightnessScale = self.gladeTree.get_widget('BrightnessScale')
		self.contrastScale = self.gladeTree.get_widget('ContrastScale')
		self.sharpnessScale = self.gladeTree.get_widget('SharpnessScale')
		self.colorAllPagesCheck = self.gladeTree.get_widget('ColorAllPagesCheck')
		
		self.titleEntry = self.gladeTree.get_widget('TitleEntry')
		self.authorEntry = self.gladeTree.get_widget('AuthorEntry')
		self.keywordsEntry = self.gladeTree.get_widget('KeywordsEntry')
		
		self.thumbnailsScrolledWindow = self.gladeTree.get_widget('ThumbnailsScrolledWindow')
		self.thumbnailsListStore = gtk.ListStore(gtk.gdk.Pixbuf)
		self.thumbnailsTreeView = gtk.TreeView(self.thumbnailsListStore)
		self.thumbnailsColumn = gtk.TreeViewColumn(None)
		self.thumbnailsCell = gtk.CellRendererPixbuf()
		self.thumbnailsColumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self.thumbnailsColumn.set_fixed_width(self.thumbnailSize)
		self.thumbnailsTreeView.append_column(self.thumbnailsColumn)
		self.thumbnailsColumn.pack_start(self.thumbnailsCell, True)
		self.thumbnailsColumn.set_attributes(self.thumbnailsCell, pixbuf=0)
		self.thumbnailsTreeView.get_selection().set_mode(gtk.SELECTION_SINGLE)
		self.thumbnailsTreeView.set_headers_visible(False)
		self.thumbnailsTreeView.set_property('can-focus', False)
		
		self.thumbnailsTreeView.set_reorderable(True)
		self.thumbnailsListStore.connect('row-inserted', self.thumbnail_inserted)
		
		self.thumbnailsTreeView.get_selection().connect('changed', self.thumbnail_selected)
		self.thumbnailsScrolledWindow.add(self.thumbnailsTreeView)
		self.thumbnailsScrolledWindow.show_all()
		
		self.previewLayout = self.gladeTree.get_widget('PreviewLayout')
		self.previewHScroll = self.gladeTree.get_widget('PreviewHScroll')
		self.previewVScroll = self.gladeTree.get_widget('PreviewVScroll')
		
		self.previewHScroll.set_adjustment(self.previewLayout.get_hadjustment())
		self.previewVScroll.set_adjustment(self.previewLayout.get_vadjustment())
		
		self.previewImageDisplay = gtk.Image()
		self.previewLayout.add(self.previewImageDisplay)
		self.previewLayout.modify_bg(gtk.STATE_NORMAL, gtk.gdk.colormap_get_system().alloc_color(gtk.gdk.Color(0, 0, 0), False, True))
		self.previewImageDisplay.show()

		self.statusbar = self.gladeTree.get_widget('ScanStatusBar')
		self.statusbar.push(self.baseStatusContextId, 'Ready')
		
		if self.get_gconf_setting('/apps/nostaples/show_toolbar', True) == False:
			self.gladeTree.get_widget('ShowToolbarMenuItem').set_active(False)
			self.toolbar.hide()
		
		if self.get_gconf_setting('/apps/nostaples/show_thumbnails', True) == False:
			self.gladeTree.get_widget('ShowThumbnailsMenuItem').set_active(False)
			self.thumbnailsScrolledWindow.hide()
		
		if self.get_gconf_setting('/apps/nostaples/show_statusbar', True) == False:
			self.gladeTree.get_widget('ShowStatusbarMenuItem').set_active(False)
			self.statusbar.hide()

		signals = {'on_ScanWindow_destroy' : self.quit,
					'on_AdjustColorsWindow_delete_event' : self.adjust_colors_close,
					'on_ScanMenuItem_activate' : self.scan_page,
					'on_SaveAsMenuItem_activate' : self.save_as,
					'on_QuitMenuItem_activate' : self.quit,
					'on_DeleteMenuItem_activate' : self.delete_selected_page,
					'on_InsertScanMenuItem_activate' : self.insert_scan,
					'on_PreferencesMenuItem_activate' : self.show_preferences,
					'on_ShowToolbarMenuItem_toggled' : self.toggle_toolbar,
					'on_ShowStatusBarMenuItem_toggled' : self.toggle_statusbar,
					'on_ShowThumbnailsMenuItem_toggled' : self.toggle_thumbnails,
					'on_ZoomInMenuItem_activate' : self.zoom_in,
					'on_ZoomOutMenuItem_activate' : self.zoom_out,
					'on_ZoomOneToOneMenuItem_activate' : self.zoom_one_to_one,
					'on_ZoomBestFitMenuItem_activate' : self.zoom_best_fit,
					'on_RotateCounterClockMenuItem_activate' : self.rotate_counter_clockwise,
					'on_RotateClockMenuItem_activate' : self.rotate_clockwise,
					'on_AdjustColorsMenuItem_toggled' : self.adjust_colors_toggle,
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
					'on_RotateCounterClockButton_clicked' : self.rotate_counter_clockwise,
					'on_RotateClockButton_clicked' : self.rotate_clockwise,
					'on_GoFirstButton_clicked' : self.goto_first_page,
					'on_GoPreviousButton_clicked' : self.goto_previous_page,
					'on_GoNextButton_clicked' : self.goto_next_page,
					'on_GoLastButton_clicked' : self.goto_last_page,
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
		
	def get_gconf_setting(self, path, default):
		'''Gets a key from gconf or, if it is not found, sets a specified default.'''
		value = self.gconfClient.get(path)
		
		if not value:
			self.set_gconf_setting(path, default)
			return default
		else:
			if value.type == gconf.VALUE_INT:
				return value.get_int()
			elif value.type == gconf.VALUE_STRING:
				return value.get_string()
			elif value.type == gconf.VALUE_FLOAT:
				return value.get_float()
			elif value.type == gconf.VALUE_BOOL:
				return value.get_bool()
			else:
				raise TypeError, 'Variable type not supported by gconf.'		
				return None				
				
	def set_gconf_setting(self, path, value):
		'''Sets a key in gconf.'''
		if type(value) is IntType:
			self.gconfClient.set_int(path, value)
		elif type(value) is StringType:
			self.gconfClient.set_string(path, value)
		elif type(value) is FloatType:
			self.gconfClient.set_float(path, value)
		elif type(value) is BooleanType:
			self.gconfClient.set_bool(path, value)
		else:
			raise TypeError, 'Variable type not supported by gconf.'
			return None

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
		
	def delete_selected_page(self, menuitem=None):
		'''Deletes the page currently selected in the thumbnail pager.'''
		if len(self.scannedPages) < 1 or self.thumbnailSelection is None:
			return
		
		del self.scannedPages[self.thumbnailSelection]
		
		deleteIter = self.thumbnailsListStore.get_iter(self.thumbnailSelection)
		self.thumbnailsListStore.remove(deleteIter)
		
		self.previewImageDisplay.clear()
		
		if self.thumbnailSelection <= len(self.scannedPages) - 1:
			self.thumbnailsTreeView.get_selection().select_path(self.thumbnailSelection)
		elif len(self.scannedPages) > 0:
			self.thumbnailsTreeView.get_selection().select_path(self.thumbnailSelection - 1)
		
	def insert_scan(self, menuitem=None):
		pass
		
	def show_preferences(self, menuitem=None):
		''''Show the preferences dialog.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		self.preferencesDialog.run()
		self.preferencesDialog.hide()
		
	def toggle_statusbar(self, menuitem):
		'''Toggles the visibility of the statusbar.'''
		if menuitem.get_active():
			self.statusbar.show()
			self.set_gconf_setting('/apps/nostaples/show_statusbar', True)
		else:
			self.statusbar.hide()
			self.set_gconf_setting('/apps/nostaples/show_statusbar', False)
		
	def toggle_toolbar(self, menuitem):
		'''Toggles the visibility of the toolbar.'''
		if menuitem.get_active():
			self.toolbar.show()
			self.set_gconf_setting('/apps/nostaples/show_toolbar', True)
		else:
			self.toolbar.hide()
			self.set_gconf_setting('/apps/nostaples/show_toolbar', False)
		
	def toggle_thumbnails(self, menuitem):
		'''Toggles the visibility of the thumbnail pager.'''
		if menuitem.get_active():
			self.thumbnailsScrolledWindow.show()
			self.set_gconf_setting('/apps/nostaples/show_thumbnails', True)
		else:
			self.thumbnailsScrolledWindow.hide()
			self.set_gconf_setting('/apps/nostaples/show_thumbnails', False)
		
	def zoom_in(self, widget=None):
		'''Zooms the preview image in by 50%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom +=  0.5
		
		if self.previewZoom > 5:
			self.previewZoom = 5
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_status()
		
	def zoom_out(self, widget=None):
		'''Zooms the preview image out by 50%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom -=  0.5
		
		if self.previewZoom < 0.5:
			self.previewZoom = 0.5
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_status()
		
	def zoom_one_to_one(self, widget=None):
		'''Zooms the preview image to exactly 100%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom =  1.0
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_status()
		
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
		self.update_status()
		
	def show_about(self, menuitem=None):
		'''Show the about dialog.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		self.aboutDialog.run()
		self.aboutDialog.hide()
		
	def update_scanner_list(self, widget=None):
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
		
		for child in self.scannerSubMenu.get_children():
			self.scannerSubMenu.remove(child)
		
		scanners = self.scannerDict.keys()
		firstItem = None
		selectedItem = None
		for i in range(len(scanners)):
			if i == 0:
				menuItem = gtk.RadioMenuItem(None, scanners[i])
				firstItem = menuItem
			else:
				menuItem = gtk.RadioMenuItem(firstItem, scanners[i])
				
			if i == 0 and self.activeScanner not in scanners:
				menuItem.set_active(True)
				selectedItem = menuItem
			
			if scanners[i] == self.activeScanner:
				menuItem.set_active(True)
				selectedItem = menuItem
			
			menuItem.connect('toggled', self.update_scanner_options)
			self.scannerSubMenu.append(menuItem)
		
		menuItem = gtk.MenuItem('Refresh List')
		menuItem.connect('activate', self.update_scanner_list)
		self.scannerSubMenu.append(menuItem)
		
		self.scannerSubMenu.show_all()
		
		# Emulate the default scanner being toggled
		self.update_scanner_options(selectedItem)

	def update_scanner_options(self, widget=None):
		'''Extracts lists of valid scanner modes and resolutions from "scanimage".'''
		assert not self.scanningThread.isAlive(), "Scanning thread should never be running when scanner options are updated."
		
		# Get the selected scanner
		toggledScanner = widget.get_children()[0].get_text()
		
		self.activeScanner = toggledScanner

		updateCmd = ' '.join(['scanimage --help -d',  self.scannerDict[self.activeScanner]])
		updatePipe = Popen(updateCmd, shell=True, stderr=STDOUT, stdout=PIPE)
		updatePipe.wait()
		
		output = updatePipe.stdout.read()		
		
		try:
			modeList = re.findall('--mode (.*) ', output)[0].split('|')
			resolutionList = re.findall('--resolution (.*)dpi ', output)[0].split('|')
		except:
			print 'Failed to parse scanner options from command: "%s"' % updateCmd
			raise
		
		for child in self.scanModeSubMenu.get_children():
			self.scanModeSubMenu.remove(child)
		
		for i in range(len(modeList)):
			if i == 0:
				menuItem = gtk.RadioMenuItem(None, modeList[i])
				firstItem = menuItem
			else:
				menuItem = gtk.RadioMenuItem(firstItem, modeList[i])
				
			if i == 0 and self.scanMode not in modeList:
				menuItem.set_active(True)
				selectedItem = menuItem
			
			if modeList[i] == self.scanMode:
				menuItem.set_active(True)
				selectedItem = menuItem
			
			menuItem.connect('toggled', self.update_scan_mode)
			self.scanModeSubMenu.append(menuItem)
			
		self.scanModeSubMenu.show_all()
		
		# Emulate the default scan mode being toggled
		self.update_scan_mode(selectedItem)		
		
		for child in self.scanResolutionSubMenu.get_children():
			self.scanResolutionSubMenu.remove(child)
		
		for i in range(len(resolutionList)):
			if i == 0:
				menuItem = gtk.RadioMenuItem(None, resolutionList[i])
				firstItem = menuItem
			else:
				menuItem = gtk.RadioMenuItem(firstItem, resolutionList[i])
				
			if i == 0 and self.scanResolution not in resolutionList:
				menuItem.set_active(True)
				selectedItem = menuItem
			
			if resolutionList[i] == self.scanResolution:
				menuItem.set_active(True)
				selectedItem = menuItem
			
			menuItem.connect('toggled', self.update_scan_resolution)
			self.scanResolutionSubMenu.append(menuItem)
			
		self.scanResolutionSubMenu.show_all()
		
		# NB: Only do this if everything else has succeeded, otherwise a crash could repeat everytime the app is started
		self.set_gconf_setting('/apps/nostaples/active_scanner', self.activeScanner)
		
		# Emulate the default scan resolution being toggled
		self.update_scan_resolution(selectedItem)
		
	
	def update_scan_mode(self, widget):
		'''Updates the internal scan mode state when a scan mode menu item is toggled.'''
		try:
			self.scanMode = widget.get_children()[0].get_text()
			self.set_gconf_setting('/apps/nostaples/scan_mode', self.scanMode)
		except:
			print 'Unable to get label text for currently selected scan mode menu item.'
			raise
		
	def update_scan_resolution(self, widget):
		'''Updates the internal scan resolution state when a scan resolution menu item is toggled.'''
		try:
			self.scanResolution = widget.get_children()[0].get_text()
			self.set_gconf_setting('/apps/nostaples/scan_resolution', self.scanResolution)
		except:
			print 'Unable to get label text for currently selected scan resolution menu item.'
			raise
		
	def rotate_counter_clockwise(self, button=None):
		'''Rotates the current page ninety degrees counter-clockwise, or all pages if "rotate all pages" is toggled on.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
		
		if self.rotateAllPagesMenuItem.get_active():
			for page in self.scannedPages:
				page.rotation += 90
		else:
			self.scannedPages[self.previewIndex].rotation += 90
			
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
		if self.rotateAllPagesMenuItem.get_active():
			for i in range(len(self.scannedPages)):			
				self.update_thumbnail(i)
		else:
			self.update_thumbnail(self.previewIndex)
		
	def rotate_clockwise(self, button=None):
		'''Rotates the current page ninety degrees clockwise, or all pages if "rotate all pages" is toggled on.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
		
		if self.rotateAllPagesMenuItem.get_active():
			for page in self.scannedPages:
				page.rotation -= 90
		else:
			self.scannedPages[self.previewIndex].rotation -= 90
			
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
		if self.rotateAllPagesMenuItem.get_active():
			for i in range(len(self.scannedPages)):			
				self.update_thumbnail(i)
		else:
			self.update_thumbnail(self.previewIndex)
			
	def adjust_colors_close(self, window, event):
		'''Closes the adjust colors dialog.'''
		self.adjustColorsWindow.hide()
		self.adjustColorsMenuItem.set_active(False)
		return True
			
	def adjust_colors_toggle(self, menuitem):
		'''Toggles the visibility of the adjust colors dialog.'''
		if self.adjustColorsMenuItem.get_active():
			self.adjustColorsWindow.show()
		else:
			self.adjustColorsWindow.hide()
		
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
			self.update_thumbnail(self.previewIndex)
		
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
			self.update_thumbnail(self.previewIndex)
		
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
			self.update_thumbnail(self.previewIndex)
			
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
			
		self.thumbnailsTreeView.get_selection().select_path(0)
		
	def goto_previous_page(self, button=None):
		'''Moves to the previous scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		if self.previewIndex < 1:
			return
			
		self.thumbnailsTreeView.get_selection().select_path(self.previewIndex - 1)
		
	def goto_next_page(self, button=None):
		'''Moves to the next scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		if self.previewIndex >= len(self.scannedPages) - 1:
			return
			
		self.thumbnailsTreeView.get_selection().select_path(self.previewIndex + 1)
		
	def goto_last_page(self, button=None):
		'''Moves to the last scanned page.'''
		if self.scanningThread.isAlive():
			self.error_box(self.scanWindow, 'Scanning is in progress...')
			return
			
		if len(self.scannedPages) < 1:
			return
			
		self.thumbnailsTreeView.get_selection().select_path(len(self.scannedPages) - 1)

	def preview_resized(self, window, rect):
		'''Catches preview display size allocations so that the preview image can be appropriately scaled to fit the display.'''
		if rect.width == self.previewWidth and rect.height == self.previewHeight:
			return
			
		self.previewWidth = rect.width
		self.previewHeight = rect.height
		
		if len(self.scannedPages) < 1:
			return
			
		if self.scanningThread.isAlive():
			return
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
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
			
			assert os.exists(pdfFIlename), 'Temporary PDF file for "%s" was not created in a timely fashion.' % page.filename
			
			input = PdfFileReader(file(pdfFilename, 'rb'))
			output.addPage(input.getPage(0))
			
			os.remove(pdfFilename)
			
		output.write(file(filename, 'w'))
		
		for page in self.scannedPages:
			os.remove(page.filename)
			
		self.thumbnailsListStore.clear()
		
		self.scannedPages = []
		self.nextScanFileIndex = 1
		self.previewIndex = 0
		self.update_status()
		
	def thumbnail_inserted(self, treemodel, path, iter):
		'''Catches when a thumbnail is inserted in the list and, if it is the result of a drag-and-drop operation, reorders the list of scanned pages to match.'''
		if self.insertIsNotDrag:
			self.insertIsNotDrag = False
			return
			
		destPath = path[0]
		
		temp = self.scannedPages[self.thumbnailSelection]
		del  self.scannedPages[self.thumbnailSelection]
		
		if destPath > self.thumbnailSelection:
			self.scannedPages.insert(destPath - 1, temp)
		else:
			self.scannedPages.insert(destPath, temp)
		
	def thumbnail_selected(self, selection):
		'''Catches when a thumbnail is selected, stores its index, and displays the proper image.'''
		selectionIter = selection.get_selected()[1]
		
		if not selectionIter:
			return
		
		scanIndex = self.thumbnailsListStore.get_path(selectionIter)[0]
		self.thumbnailSelection = scanIndex
		self.jump_to_page(scanIndex)
		
	# Functions not tied to a signal
	
	def update_status(self):
		'''Updates the status bar with the current page number and zoom percentage.'''
		self.statusbar.pop(self.previewStatusContextId)
		
		if len(self.scannedPages) > 0:
			self.statusbar.push(self.previewStatusContextId,'Page %i of %i\t%i%%' % (self.previewIndex + 1, len(self.scannedPages), int(self.previewZoom * 100)))
		
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
		
	def update_thumbnail(self, index):
		'''Updates a thumbnail image to match changes in the preview image.'''
		iter = self.thumbnailsListStore.get_iter(index)
		thumbnail = self.scannedPages[index].get_thumbnail(self.thumbnailSize)
		self.thumbnailsListStore.set_value(iter, 0, thumbnail)
		
	def jump_to_page(self, index):
		'''Moves to a specified scanned page.'''
		assert index >= 0 and index < len(self.scannedPages), 'Page index out of bounds.'
			
		self.previewIndex = index
		
		self.brightnessScale.set_value(self.scannedPages[self.previewIndex].brightness)
		self.contrastScale.set_value(self.scannedPages[self.previewIndex].contrast)
		self.sharpnessScale.set_value(self.scannedPages[self.previewIndex].sharpness)
		
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
class ScanningThread(threading.Thread):
	'''A Thread object for scanning documents without hanging the GUI.'''
	
	def __init__(self, app):
		self.app = app
		self.stopThreadEvent = threading.Event()
		
		threading.Thread.__init__(self)
	
	def run(self):
		'''Scans a page with "scanimage" and appends it to the end of the current document.'''
		gtk.gdk.threads_enter()
		
		self.app.statusbar.push(self.app.scanStatusContextId,'Scanning...')
		self.app.previewImageDisplay.clear()
		
		if not self.app.colorAllPagesCheck.get_active():
			self.app.brightnessScale.set_value(1.0)
			self.app.contrastScale.set_value(1.0)
			self.app.sharpnessScale.set_value(1.0)
		gtk.gdk.threads_leave()
		
		assert self.app.scanMode != None, 'Attempting to scan with no scan mode selected.'
		assert self.app.scanResolution != None, 'Attempting to scan with no scan resolution selected.'
		assert self.app.activeScanner != None, 'Attempting to scan with no scanner selected.'
		
		scanProgram = 'scanimage --format=pnm'
		modeFlag = ' '.join(['--mode', self.app.scanMode])
		resolutionFlag = ' '.join(['--resolution', self.app.scanResolution])
		scannerFlag = ' '.join(['-d', self.app.scannerDict[self.app.activeScanner]])
		outputFile = '>scan%i.pnm' % self.app.nextScanFileIndex
		scanCmd = ' '.join([scanProgram, modeFlag, resolutionFlag, scannerFlag, outputFile])
		
		print 'Scanning with command: "%s"' % scanCmd
		scanPipe = Popen(scanCmd, shell=True, stderr=STDOUT, stdout=PIPE)
		
		while scanPipe.poll() == None:
			if self.stopThreadEvent.isSet():
				os.kill(scanPipe.pid, signal.SIGTERM)
				print 'Scan terminated'
				self.app.render_preview()
				self.app.statusbar.pop(self.app.scanStatusContextId)
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
		
		self.app.insertIsNotDrag = True
		self.app.thumbnailsListStore.append([newPage.get_thumbnail(self.app.thumbnailSize)])
		self.app.thumbnailsTreeView.get_selection().select_path(len(self.app.scannedPages) - 1)
		
		self.app.statusbar.pop(self.app.scanStatusContextId)	
		
		gtk.gdk.threads_leave()
		
	def stop(self):
		'''Stops a scan that is currently in progress.'''
		self.stopThreadEvent.set()
		self.app.statusbar.pop(self.app.scanStatusContextId)
		
class NoStaplesPdfFileWriter(PdfFileWriter):
	'''A subclass of a PyPdf PdfFileWriter that adds support for custom meta-data.'''
	
	def __init__(self, title, author, keywords):
		'''Overrides the built in PdfFileWriter constructor to add support for custom metadata.'''
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
		'''Constructs a Page object and pulls a local copy of the image from the scan file.'''
		assert os.path.exists(filename), 'Image file "%s" could not be found.' % filename
		
		self.filename = filename
		self.rotation = 0
		self.brightness = 1.0
		self.contrast = 1.0
		self.sharpness = 1.0
		
		self.rawPixbuf = gtk.gdk.pixbuf_new_from_file(self.filename)

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
		'''Generates a GTK Pixbuf that has had rotation and color adjustments applied to it (i.e. a working copy).'''
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
		
	def get_thumbnail(self, size):
		'''Generates a GTK Pixbuf that hashad rotation and color adjustments applied to it and has been scaled down to fit the thumbnail pager.'''
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
		
# Main loop

if __name__ == '__main__':
	app = NoStaples()
	gtk.gdk.threads_enter()
	gtk.main()
	gtk.gdk.threads_leave()