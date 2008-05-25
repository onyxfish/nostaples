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
import threading
import time
import gtk
import gtk.glade
import gobject
import Image, ImageEnhance
from pyPdf.pdf import *

import constants
import state
import page
import gui
import scanning

gtk.gdk.threads_init()

def threaded(func):
	'''Threading function decorator.'''
	def proxy(*args, **kwargs):
		t = threading.Thread(target=func, args=args, kwargs=kwargs)
		t.start()
		return t
	return proxy
    
class NoStaples:
	'''NoStaples' main application class.'''

	def __init__(self):
		'''Sets up all application variables (including loading saved settings), loads the interface via glade, connects signals, and then shows the scanning window.'''
		self.stateEngine = state.GConfStateEngine()
		self.__init_states()
		
		self.scannerDict = {}	# Keys are human readable scanner descriptions, Values are sane-backend descriptors
		self.activeScanner = self.stateEngine.get_state('active_scanner')
		self.scanMode = self.stateEngine.get_state('scan_mode')
		self.scanResolution = self.stateEngine.get_state('scan_resolution')
		self.scannedPages = []	# List of Page objects
		self.nextScanFileIndex = 0
		self.previewIndex = 0
		self.previewPixbuf = None
		self.previewWidth = 0
		self.previewHeight = 0
		self.previewZoom = 1.0
		self.previewIsBestFit = True
		self.previewDragStart = (0,0)
		self.thumbnailSize = self.stateEngine.get_state('thumbnail_size')
		self.thumbnailSelection = None
		self.insertIsNotDrag = False
		self.scanEvent = threading.Event()
		self.cancelScanEvent = threading.Event()
		self.quitEvent = threading.Event()
		
		self.gui = gui.GtkGUI(self, 'nostaples.glade')
		
		self.update_scanner_list()
		
	def __init_states(self):
		'''Initializes each state that is tracked in the state engine, setting up default values and callbacks.'''
		self.stateEngine.init_state('active_scanner', constants.DEFAULT_ACTIVE_SCANNER)
		self.stateEngine.init_state('scan_mode', constants.DEFAULT_SCAN_MODE)
		self.stateEngine.init_state('scan_resolution', constants.DEFAULT_SCAN_RESOLUTION)
		self.stateEngine.init_state('thumbnail_size', constants.DEFAULT_THUMBNAIL_SIZE)
		self.stateEngine.init_state('show_toolbar', True, self.toggle_toolbar)
		self.stateEngine.init_state('show_thumbnails', True, self.toggle_thumbnails)
		self.stateEngine.init_state('show_statusbar', True, self.toggle_statusbar)
		self.stateEngine.init_state('save_path', os.path.expanduser('~'))		
		
	# Functions called by gui signal handlers
	
	def quit(self):
		'''Called when ScanWindow is destroyed to cleanup threads and files.'''
		self.quitEvent.set()
			
		for page in self.scannedPages:
			os.remove(page.filename)
		
		gtk.main_quit()
		
	def scan_page(self):
		'''Starts the scanning thread.'''
		assert not self.scanEvent.isSet(), 'Scanning in progress.'
		self.scan_thread(len(self.scannedPages))
		
	def save_as(self):
		'''Gets PDF Metadata from the user, prompts for a filename, and saves the document to PDF.'''
		assert not self.scanEvent.isSet(), 'Scanning in progress.'
			
		if len(self.scannedPages) < 1:
			self.error_box(self.scanWindow, 'No pages have been scanned.')
			return
			
		title = ''
		author = ''
		keywords =''
		
		while title == '':
			response = self.gui.metadataDialog.run()
		
			if response != 1:
				self.gui.metadataDialog.hide()
				return
			
			title = unicode(self.gui.titleEntry.get_text())
			author = unicode(self.gui.authorEntry.get_text())
			keywords = unicode(self.gui.keywordsEntry.get_text())
		
			if title == '':
				self.gui.error_box(self.scanWindow, 'You must provide a title for this document.')
			
		self.gui.metadataDialog.hide()
		
		filter = gtk.FileFilter()
		filter.set_name('PDF Files')
		filter.add_mime_type('application/pdf')
		filter.add_pattern('*.pdf')
		self.saveDialog.add_filter(filter)
		
		savePath = self.stateEngine.get_state('save_path')
		if not os.path.exists(savePath):
			savePath = os.path.expanduser('~')
		filename = ''.join([title.replace(' ', '-').lower(), '.pdf'])
		self.gui.saveDialog.set_current_folder(savePath)
		self.gui.saveDialog.set_current_name(filename)
		
		response = self.gui.saveDialog.run()
		self.gui.saveDialog.hide()
		
		if response != 1:
			return
		
		filename = self.gui.saveDialog.get_filename()
		
		output = NoStaplesPdfFileWriter(title, author, keywords)
			
		for page in self.scannedPages:
			tempImage = Image.open(page.filename)
			pdfFilename = ''.join([page.filename[:-4], '.pdf'])
			
			rotatedImage = tempImage.rotate(page.rotation)
			brightenedImage = ImageEnhance.Brightness(rotatedImage).enhance(page.brightness)
			contrastedImage = ImageEnhance.Contrast(brightenedImage).enhance(page.contrast)
			sharpenedImage = ImageEnhance.Sharpness(contrastedImage).enhance(page.sharpness)
			
			sharpenedImage.save(pdfFilename)
			
			assert os.path.exists(pdfFilename), 'Temporary PDF file for "%s" was not created in a timely fashion.' % page.filename
			
			input = PdfFileReader(file(pdfFilename, 'rb'))
			output.addPage(input.getPage(0))
			
			os.remove(pdfFilename)
			
		output.write(file(filename, 'w'))
		self.stateEngine.set_state('save_path', self.saveDialog.get_current_folder())
		
		for page in self.scannedPages:
			os.remove(page.filename)
		
		self.gui.previewImageDisplay.clear()
		self.gui.thumbnailsListStore.clear()
		
		self.scannedPages = []
		self.nextScanFileIndex = 1
		self.previewIndex = 0
		self.update_status()
		
	def delete_selected_page(self):
		'''Deletes the page currently selected in the thumbnail pager.'''
		if len(self.scannedPages) < 1 or self.thumbnailSelection is None:
			return
	
		del self.scannedPages[self.thumbnailSelection]
		
		deleteIter = self.gui.thumbnailsListStore.get_iter(self.thumbnailSelection)
		self.gui.thumbnailsListStore.remove(deleteIter)
		
		self.gui.previewImageDisplay.clear()
		
		if self.thumbnailSelection <= len(self.scannedPages) - 1:
			self.gui.thumbnailsTreeView.get_selection().select_path(self.thumbnailSelection)
		elif len(self.scannedPages) > 0:
			self.gui.thumbnailsTreeView.get_selection().select_path(self.thumbnailSelection - 1)
		
	def insert_scan(self):
		'''Scans a page and inserts it before the current selected thumbnail.'''
		assert not self.scanEvent.isSet(), 'Scanning in progress.'
		self.scan_thread(self.thumbnailSelection)
		
	def show_preferences(self):
		'''Show the preferences dialog.'''
		assert not self.scanEvent.isSet(), 'Scanning in progress.'
			
		self.gui.preferencesDialog.run()
		self.gui.preferencesDialog.hide()
		
	def toggle_toolbar(self):
		'''Toggles the visibility of the toolbar.'''
		if self.stateEngine.get_state('show_toolbar'):
			self.gui.toolbar.show()
		else:
			self.gui.toolbar.hide()
		
	def toggle_thumbnails(self):
		'''Toggles the visibility of the thumbnail pager.'''
		if self.stateEngine.get_state('show_thumbnails'):
			self.gui.thumbnailsScrolledWindow.show()
		else:
			self.gui.thumbnailsScrolledWindow.hide()
		
	def toggle_statusbar(self):
		'''Toggles the visibility of the statusbar.'''
		if self.stateEngine.get_state('show_statusbar'):
			self.gui.statusbar.show()
		else:
			self.gui.statusbar.hide()
		
	def zoom_in(self):
		'''Zooms the preview image in by 50%.'''
		if len(self.scannedPages) < 1:
			return
			
		if self.previewZoom == 5:
			return
			
		self.previewZoom +=  0.5
		
		if self.previewZoom > 5:
			self.previewZoom = 5
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_status()
		
	def zoom_out(self):
		'''Zooms the preview image out by 50%.'''
		if len(self.scannedPages) < 1:
			return
			
		if self.previewZoom == 0.5:
			return
			
		self.previewZoom -=  0.5
		
		if self.previewZoom < 0.5:
			self.previewZoom = 0.5
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_status()
		
	def zoom_one_to_one(self):
		'''Zooms the preview image to exactly 100%.'''
		if len(self.scannedPages) < 1:
			return
			
		self.previewZoom =  1.0
			
		self.previewIsBestFit = False
			
		self.render_preview()
		self.update_status()
		
	def zoom_best_fit(self):
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
		
	def rotate_counter_clockwise(self):
		'''Rotates the current page ninety degrees counter-clockwise, or all pages if "rotate all pages" is toggled on.'''
		if len(self.scannedPages) < 1:
			return
		
		if self.gui.rotateAllPagesMenuItem.get_active():
			for page in self.scannedPages:
				page.rotation += 90
		else:
			self.scannedPages[self.previewIndex].rotation += 90
			
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_transformed_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
		if self.gui.rotateAllPagesMenuItem.get_active():
			for i in range(len(self.scannedPages)):			
				self.update_thumbnail(i)
		else:
			self.update_thumbnail(self.previewIndex)
		
	def rotate_clockwise(self):
		'''Rotates the current page ninety degrees clockwise, or all pages if "rotate all pages" is toggled on.'''
		if len(self.scannedPages) < 1:
			return
		
		if self.gui.rotateAllPagesMenuItem.get_active():
			for page in self.scannedPages:
				page.rotation -= 90
		else:
			self.scannedPages[self.previewIndex].rotation -= 90
			
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_transformed_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
		if self.gui.rotateAllPagesMenuItem.get_active():
			for i in range(len(self.scannedPages)):			
				self.update_thumbnail(i)
		else:
			self.update_thumbnail(self.previewIndex)
					
	def adjust_colors_toggle(self):
		'''Toggles the visibility of the adjust colors dialog.'''
		if self.gui.adjustColorsMenuItem.get_active():
			self.gui.adjustColorsWindow.show()
		else:
			self.gui.adjustColorsWindow.hide()
	
	def update_scan_mode(self, widget):
		'''Updates the internal scan mode state when a scan mode menu item is toggled.'''
		try:
			self.scanMode = widget.get_children()[0].get_text()
			self.stateEngine.set_state('scan_mode', self.scanMode)
		except:
			print 'Unable to get label text for currently selected scan mode menu item.'
			raise
		
	def update_scan_resolution(self, widget):
		'''Updates the internal scan resolution state when a scan resolution menu item is toggled.'''
		try:
			self.scanResolution = widget.get_children()[0].get_text()
			self.stateEngine.set_state('scan_resolution', self.scanResolution)
		except:
			print 'Unable to get label text for currently selected scan resolution menu item.'
			raise
		
	def goto_first_page(self):
		'''Moves to the first scanned page.'''
		if len(self.scannedPages) < 1:
			return
			
		self.gui.thumbnailsTreeView.get_selection().select_path(0)
		
	def goto_previous_page(self):
		'''Moves to the previous scanned page.'''
		if len(self.scannedPages) < 1:
			return
			
		if self.previewIndex < 1:
			return
			
		self.gui.thumbnailsTreeView.get_selection().select_path(self.previewIndex - 1)
		
	def goto_next_page(self):
		'''Moves to the next scanned page.'''
		if len(self.scannedPages) < 1:
			return
			
		if self.previewIndex >= len(self.scannedPages) - 1:
			return
			
		self.gui.thumbnailsTreeView.get_selection().select_path(self.previewIndex + 1)
		
	def goto_last_page(self):
		'''Moves to the last scanned page.'''
		if len(self.scannedPages) < 1:
			return
			
		self.gui.thumbnailsTreeView.get_selection().select_path(len(self.scannedPages) - 1)
		
	def show_about(self):
		'''Show the about dialog.'''			
		self.gui.aboutDialog.run()
		self.gui.aboutDialog.hide()
		
	def update_brightness(self):
		'''Updates the brightness of the current page, or all pages if the "ColorAllPagesCheck" is toggled on.'''
		if len(self.scannedPages) < 1:
			return
			
		self.gui.adjustColorsWindow.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			
		self.scannedPages[self.previewIndex].brightness = self.gui.brightnessScale.get_value()
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_transformed_pixbuf()
		self.render_preview()
		self.update_thumbnail(self.previewIndex)
		
		if self.gui.colorAllPagesCheck.get_active() and len(self.scannedPages) > 1:
			for index in range(len(self.scannedPages)):
				if index != self.previewIndex:
					self.scannedPages[index].brightness = self.gui.brightnessScale.get_value()
					self.update_thumbnail(index)
					
		self.gui.adjustColorsWindow.window.set_cursor(None)
		
	def update_contrast(self):		
		'''Updates the contrast of the current page, or all pages if the "ColorAllPagesCheck" is toggled on.'''	
		if len(self.scannedPages) < 1:
			return
			
		self.scannedPages[self.previewIndex].contrast = self.gui.contrastScale.get_value()
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_transformed_pixbuf()
		self.render_preview()
		self.update_thumbnail(self.previewIndex)
		
		if self.gui.colorAllPagesCheck.get_active() and len(self.scannedPages) > 1:
			for index in range(len(self.scannedPages)):
				if index != self.previewIndex:
					self.scannedPages[index].contrast = self.gui.contrastScale.get_value()
					self.update_thumbnail(index)
		
	def update_sharpness(self):	
		'''Updates the sharpness of the current page, or all pages if the "ColorAllPagesCheck" is toggled on.'''		
		if len(self.scannedPages) < 1:
			return
		
		self.scannedPages[self.previewIndex].sharpness = self.gui.sharpnessScale.get_value()
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_transformed_pixbuf()
		self.render_preview()
		self.update_thumbnail(self.previewIndex)
		
		if self.gui.colorAllPagesCheck.get_active() and len(self.scannedPages) > 1:
			for index in range(len(self.scannedPages)):
				if index != self.previewIndex:
					self.scannedPages[index].sharpness = self.gui.sharpnessScale.get_value()
					self.update_thumbnail(index)
			
	def color_all_pages_toggled(self):
		'''Catches the ColorAllPagesCheck being toggled on so that all per-page settings can be immediately synchronized.'''
		if self.gui.colorAllPagesCheck.get_active():
			for index in range(len(self.scannedPages)):
				if index != self.previewIndex:
					self.scannedPages[index].brightness = self.gui.brightnessScale.get_value()
					self.scannedPages[index].contrast = self.gui.contrastScale.get_value()
					self.scannedPages[index].sharpness = self.gui.sharpnessScale.get_value()
					self.update_thumbnail(index)

	def preview_resized(self, rect):
		'''Catches preview display size allocations so that the preview image can be appropriately scaled to fit the display.'''
		if rect.width == self.previewWidth and rect.height == self.previewHeight:
			return
			
		self.previewWidth = rect.width
		self.previewHeight = rect.height
		
		if len(self.scannedPages) < 1:
			return
			
		if self.scanEvent.isSet():
			return
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
		
	def preview_button_pressed(self, event):
		'''Catches button presses on the preview display and traps the coords for dragging.'''
		if len(self.scannedPages) < 1:
			return
		
		if event.button == 3:
			self.zoomDragStartX, self.zoomDragStartY = event.x, event.y
			
	def preview_button_released(self, event):
		if len(self.scannedPages) < 1:
			return
		
		if event.button == 3:				
			# Transform to absolute coords
			x1 = self.zoomDragStartX / self.previewZoom
			y1 = self.zoomDragStartY / self.previewZoom
			x2 = event.x / self.previewZoom
			y2 = event.y / self.previewZoom
			
			# Swizzle values if coords are reversed
			if x2 < x1:
				x1, x2 = x2, x1
				
			if y2 < y1:
				y1, y2 = y2, y1
			
			# Calc width and height
			w = x2 - x1
			h = y2 - y1
			
			# Calculate centering offset
			targetWidth =  self.previewPixbuf.get_width() * self.previewZoom
			targetHeight =  self.previewPixbuf.get_height() * self.previewZoom
			
			shiftX = int((self.previewWidth - targetWidth) / 2)
			if shiftX < 0:
				shiftX = 0
			shiftY = int((self.previewHeight - targetHeight) / 2)
			if shiftY < 0:
				shiftY = 0
			
			# Compensate for centering
			x1 -= shiftX / self.previewZoom
			y1 -= shiftY / self.previewZoom
			
			# Determine correct zoom to fit region
			if w > h:
				self.previewZoom = self.previewWidth / w
			else:
				self.previewZoom = self.previewHeight / h
				
			# Cap zoom at 500%
			if self.previewZoom > 5.0:
				self.previewZoom = 5.0
			
			# Transform to relative coords
			tx = int(x1 * self.previewZoom)
			ty = int(y1 * self.previewZoom)
			
			self.previewIsBestFit = False
			self.render_preview()
			
			self.gui.previewLayout.get_hadjustment().set_value(tx)
			self.gui.previewLayout.get_vadjustment().set_value(ty)
			
			self.update_status()
		
	def preview_mouse_moved(self, event):
		'''Handles click-and-drag behavior for the preview display.'''
		if len(self.scannedPages) < 1:
			return
			
		if event.is_hint:
			x, y, state = event.window.get_pointer()
		else:
			state = event.state
			
		x, y = event.x_root, event.y_root
		
		if (state & gtk.gdk.BUTTON2_MASK) or (state & gtk.gdk.BUTTON1_MASK):
			hAdjust = self.gui.previewLayout.get_hadjustment()
			newX = hAdjust.value + (self.previewDragStart[0] - x)
			if newX >= hAdjust.lower and newX <= hAdjust.upper - hAdjust.page_size:
				hAdjust.set_value(newX)
				
			vAdjust = self.gui.previewLayout.get_vadjustment()
			newY = vAdjust.value + (self.previewDragStart[1] - y)
			if newY >= vAdjust.lower and newY <= vAdjust.upper - vAdjust.page_size:
				vAdjust.set_value(newY)
			
		self.previewDragStart = (x, y)
		
	def preview_scrolled(self, event):
		if len(self.scannedPages) < 1:
			return
		
		currentX = self.gui.previewLayout.get_hadjustment()
		currentY = self.gui.previewLayout.get_vadjustment()
		newX = currentX.value
		newY = currentY.value
		
		if event.direction == gtk.gdk.SCROLL_UP:
			self.zoom_in()
			#~ newY = currentY.value - currentY.page_size
		elif event.direction == gtk.gdk.SCROLL_DOWN:
			self.zoom_out()
			#~ newY = currentY.value + currentY.page_size
		#~ elif event.direction == gtk.gdk.SCROLL_LEFT:
			#~ newX = currentX.value - currentX.page_size
		#~ elif event.direction == gtk.gdk.SCROLL_RIGHT:
			#~ newX = currentX.value + currentX.page_size
			
		#~ if newX != currentX.value:
			#~ if newX < currentX.lower:
				#~ newX = currentX.lower
			#~ elif newX > currentX.upper - currentX.page_size:
				#~ newX = currentX.upper - currentX.page_size
			#~ currentX.set_value(newX)
			#~ self.gui.previewLayout.set_hadjustment(currentX)
		#~ if newY != currentY.value:
			#~ if newY < currentY.lower:
				#~ newY = currentY.lower
			#~ elif newY > currentY.upper - currentY.page_size:
				#~ newY = currentY.upper - currentY.page_size
			#~ currentY.set_value(newY)
			#~ self.gui.previewLayout.set_vadjustment(currentY)		
			
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
		
		scanIndex = self.gui.thumbnailsListStore.get_path(selectionIter)[0]
		self.thumbnailSelection = scanIndex
		self.jump_to_page(scanIndex)
		
	# Functions not called from gui signal handlers
			
	def add_page(self, index, page):
		'''Appends or inserts a page into the list of scanned pages.'''
		self.insertIsNotDrag = True
		
		if not index:
			index = 0
		
		if index > len(self.scannedPages) - 1:
			self.scannedPages.append(page)
			self.gui.thumbnailsListStore.append([page.get_thumbnail_pixbuf(self.thumbnailSize)])
			self.gui.thumbnailsTreeView.get_selection().select_path(len(self.scannedPages) - 1)
		else:
			self.scannedPages.insert(index, page)
			self.gui.thumbnailsListStore.insert(index, [page.get_thumbnail_pixbuf(self.thumbnailSize)])
			self.gui.thumbnailsTreeView.get_selection().select_path(index)
		
	def jump_to_page(self, index):
		'''Moves to a specified scanned page.'''
		assert index >= 0 and index < len(self.scannedPages), 'Page index out of bounds.'
			
		self.previewIndex = index
		
		self.gui.brightnessScale.set_value(self.scannedPages[self.previewIndex].brightness)
		self.gui.contrastScale.set_value(self.scannedPages[self.previewIndex].contrast)
		self.gui.sharpnessScale.set_value(self.scannedPages[self.previewIndex].sharpness)
		
		self.previewPixbuf = self.scannedPages[self.previewIndex].get_transformed_pixbuf()
		
		if self.previewIsBestFit:
			self.zoom_best_fit()
		else:
			self.render_preview()
			self.update_status()
	
	def update_status(self):
		'''Updates the status bar with the current page number and zoom percentage.'''
		self.gui.statusbar.pop(constants.STATUSBAR_PREVIEW_CONTEXT_ID)
		
		if len(self.scannedPages) > 0:
			self.gui.statusbar.push(constants.STATUSBAR_PREVIEW_CONTEXT_ID,'Page %i of %i\t%i%%' % (self.previewIndex + 1, len(self.scannedPages), int(self.previewZoom * 100)))
		
	def update_thumbnail(self, index):
		'''Updates a thumbnail image to match changes in the preview image.'''
		iter = self.gui.thumbnailsListStore.get_iter(index)
		thumbnail = self.scannedPages[index].get_thumbnail_pixbuf(self.thumbnailSize)
		self.gui.thumbnailsListStore.set_value(iter, 0, thumbnail)
		
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
		self.gui.previewLayout.set_size(targetWidth, targetHeight)
		
		# Center preview
		shiftX = int((self.previewWidth - targetWidth) / 2)
		if shiftX < 0:
			shiftX = 0
		shiftY = int((self.previewHeight - targetHeight) / 2)
		if shiftY < 0:
			shiftY = 0
		self.gui.previewLayout.move(self.gui.previewImageDisplay, shiftX, shiftY)
		
		# Show/hide scrollbars
		if targetWidth > self.previewWidth:
			self.gui.previewHScroll.show()
		else:
			self.gui.previewHScroll.hide()
			
		if targetHeight > self.previewHeight:
			self.gui.previewVScroll.show()
		else:
			self.gui.previewVScroll.hide()
		
		# Render updated preview
		self.gui.previewImageDisplay.set_from_pixbuf(pixbuf)
					
	def update_scanner_list(self, widget=None):
		'''Populates a menu with a list of available scanners.'''
		assert not self.scanEvent.isSet(), 'Scanning in progress.'
		
		self.scannerDict = scanning.get_available_scanners()
		
		for child in self.gui.scannerSubMenu.get_children():
			self.gui.scannerSubMenu.remove(child)
		
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
			self.gui.scannerSubMenu.append(menuItem)
		
		menuItem = gtk.MenuItem('Refresh List')
		menuItem.connect('activate', self.update_scanner_list)
		self.gui.scannerSubMenu.append(menuItem)
		
		self.gui.scannerSubMenu.show_all()
		
		# Emulate the default scanner being toggled
		self.update_scanner_options(selectedItem)

	def update_scanner_options(self, widget=None):
		'''Populates a menu with a list of available options for the currently selected scanner.'''
		assert not self.scanEvent.isSet(), 'Scanning in progress.'
		
		# Get the selected scanner
		toggledScanner = widget.get_children()[0].get_text()
		
		self.activeScanner = toggledScanner			
		modeList, resolutionList = scanning.get_scanner_options(self.scannerDict[self.activeScanner])
		
		for child in self.gui.scanModeSubMenu.get_children():
			self.gui.scanModeSubMenu.remove(child)
		
		if not modeList:
			menuItem = gtk.MenuItem("No Scan Modes")
			menuItem.set_sensitive(False)
			self.gui.scanModeSubMenu.append(menuItem)
		else:		
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
				self.gui.scanModeSubMenu.append(menuItem)
			
		self.gui.scanModeSubMenu.show_all()
		
		# Emulate the default scan mode being toggled
		self.update_scan_mode(selectedItem)		
		
		for child in self.gui.scanResolutionSubMenu.get_children():
			self.gui.scanResolutionSubMenu.remove(child)
		
		if not resolutionList:
			menuItem = gtk.MenuItem("No Resolutions")
			self.gui.scanResolutionSubMenu.append(menuItem)
			menuItem.set_sensitive(False)
		else:		
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
				self.gui.scanResolutionSubMenu.append(menuItem)
			
		self.gui.scanResolutionSubMenu.show_all()
		
		# NB: Only do this if everything else has succeeded, otherwise a crash could repeat everytime the app is started
		self.stateEngine.set_state('active_scanner', self.activeScanner)
		
		# Emulate the default scan resolution being toggled
		self.update_scan_resolution(selectedItem)
	
	@threaded
	def scan_thread(self, index):
		'''Scans a page with "scanimage" and appends it to the end of the current document.'''
		self.scanEvent.set()
		
		gtk.gdk.threads_enter()
		
		self.gui.set_file_and_scan_controls_sensitive(False)
		self.gui.statusbar.push(constants.STATUSBAR_SCAN_CONTEXT_ID,'Scanning...')
			
		gtk.gdk.threads_leave()
		
		assert self.scanMode != None, 'Attempting to scan with no scan mode selected.'
		assert self.scanResolution != None, 'Attempting to scan with no scan resolution selected.'
		assert self.activeScanner != None, 'Attempting to scan with no scanner selected.'
		
		scanFilename = 'scan%i.pnm' % self.nextScanFileIndex
		result = scanning.scan_to_file(self.scannerDict[self.activeScanner], self.scanMode, self.scanResolution, scanFilename)
		
		if result == scanning.SCAN_FAILURE:
			# TODO - better notification here
			gtk.gdk.threads_enter()
			self.gui.statusbar.pop(constants.STATUSBAR_SCAN_CONTEXT_ID)
			gtk.gdk.threads_leave()
			return
			
		if self.quitEvent.isSet():
			return
			
		if self.cancelScanEvent.isSet():
			gtk.gdk.threads_enter()
			self.gui.statusbar.pop(constants.STATUSBAR_SCAN_CONTEXT_ID)
			gtk.gdk.threads_leave()
			return
		
		self.nextScanFileIndex += 1
		
		scanPage = page.Page(scanFilename)
		
		gtk.gdk.threads_enter()
		
		if not self.gui.colorAllPagesCheck.get_active():
			self.gui.brightnessScale.set_value(1.0)
			self.gui.contrastScale.set_value(1.0)
			self.gui.sharpnessScale.set_value(1.0)
			
		scanPage.brightness = self.gui.brightnessScale.get_value()
		scanPage.contrast = self.gui.contrastScale.get_value()
		scanPage.sharpness = self.gui.sharpnessScale.get_value()
		
		self.add_page(index, scanPage)
		
		self.gui.statusbar.pop(constants.STATUSBAR_SCAN_CONTEXT_ID)	
		self.gui.set_file_and_scan_controls_sensitive(True)
		
		gtk.gdk.threads_leave()
		
		self.scanEvent.clear()
		
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
		
# Main loop

if __name__ == '__main__':
	app = NoStaples()
	gtk.gdk.threads_enter()
	gtk.main()
	gtk.gdk.threads_leave()