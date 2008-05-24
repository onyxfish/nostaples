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

import gtk
import gtk.glade
import gobject

import constants
import state

class GtkGUI():
	
	def __init__(self, app, gladeFile):
		self.app = app
		
		self.gladeFile = gladeFile
		self.gladeTree = gtk.glade.XML(self.gladeFile)
		
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
		#self.thumbnailsColumn.set_fixed_width(self.thumbnailSize)
		self.thumbnailsColumn.set_fixed_width(128)
		self.thumbnailsTreeView.append_column(self.thumbnailsColumn)
		self.thumbnailsColumn.pack_start(self.thumbnailsCell, True)
		self.thumbnailsColumn.set_attributes(self.thumbnailsCell, pixbuf=0)
		self.thumbnailsTreeView.get_selection().set_mode(gtk.SELECTION_SINGLE)
		self.thumbnailsTreeView.set_headers_visible(False)
		self.thumbnailsTreeView.set_property('can-focus', False)
		
		self.thumbnailsTreeView.set_reorderable(True)
		self.thumbnailsListStore.connect('row-inserted', self.on_ThumbnailsListStore_row_inserted)
		self.thumbnailsTreeView.get_selection().connect('changed', self.on_ThumbnailsTreeSelection_changed)
		
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
		self.statusbar.push(constants.STATUSBAR_BASE_CONTEXT_ID, 'Ready')

		signals = {'on_ScanWindow_destroy' : self.on_ScanWindow_destroy,
					'on_AdjustColorsWindow_delete_event' : self.on_AdjustColorsWindow_delete_event,
					'on_ScanMenuItem_activate' : self.on_ScanMenuItem_activate,
					'on_SaveAsMenuItem_activate' : self.on_SaveAsMenuItem_activate,
					'on_QuitMenuItem_activate' : self.on_QuitMenuItem_activate,
					'on_DeleteMenuItem_activate' : self.on_DeleteMenuItem_activate,
					'on_InsertScanMenuItem_activate' : self.on_InsertScanMenuItem_activate,
					'on_PreferencesMenuItem_activate' : self.on_PreferencesMenuItem_activate,
					'on_ShowToolbarMenuItem_toggled' : self.on_ShowToolbarMenuItem_toggled,
					'on_ShowStatusBarMenuItem_toggled' : self.on_ShowStatusBarMenuItem_toggled,
					'on_ShowThumbnailsMenuItem_toggled' : self.on_ShowThumbnailsMenuItem_toggled,
					'on_ZoomInMenuItem_activate' : self.on_ZoomInMenuItem_activate,
					'on_ZoomOutMenuItem_activate' : self.on_ZoomOutMenuItem_activate,
					'on_ZoomOneToOneMenuItem_activate' : self.on_ZoomOneToOneMenuItem_activate,
					'on_ZoomBestFitMenuItem_activate' : self.on_ZoomBestFitMenuItem_activate,
					'on_RotateCounterClockMenuItem_activate' : self.on_RotateCounterClockMenuItem_activate,
					'on_RotateClockMenuItem_activate' : self.on_RotateClockMenuItem_activate,
					'on_AdjustColorsMenuItem_toggled' : self.on_AdjustColorsMenuItem_toggled,
					'on_GoFirstMenuItem_activate' : self.on_GoFirstMenuItem_activate,
					'on_GoPreviousMenuItem_activate' : self.on_GoPreviousMenuItem_activate,
					'on_GoNextMenuItem_activate' : self.on_GoNextMenuItem_activate,
					'on_GoLastMenuItem_activate' : self.on_GoLastMenuItem_activate,
					'on_AboutMenuItem_activate' : self.on_AboutMenuItem_activate,
					'on_ScanButton_clicked' : self.on_ScanButton_clicked,
					'on_SaveAsButton_clicked' : self.on_SaveAsButton_clicked,
					'on_ZoomInButton_clicked' : self.on_ZoomInButton_clicked,
					'on_ZoomOutButton_clicked' : self.on_ZoomOutButton_clicked,
					'on_ZoomOneToOneButton_clicked' : self.on_ZoomOneToOneButton_clicked,
					'on_ZoomBestFitButton_clicked' : self.on_ZoomBestFitButton_clicked,
					'on_RotateCounterClockButton_clicked' : self.on_RotateCounterClockButton_clicked,
					'on_RotateClockButton_clicked' : self.on_RotateClockButton_clicked,
					'on_GoFirstButton_clicked' : self.on_GoFirstButton_clicked,
					'on_GoPreviousButton_clicked' : self.on_GoPreviousButton_clicked,
					'on_GoNextButton_clicked' : self.on_GoNextButton_clicked,
					'on_GoLastButton_clicked' : self.on_GoLastButton_clicked,
					'on_BrightnessScale_value_changed' : self.on_BrightnessScale_value_changed,		
					'on_ContrastScale_value_changed' : self.on_ContrastScale_value_changed,		
					'on_SharpnessScale_value_changed' : self.on_SharpnessScale_value_changed,
					'on_ColorAllPagesCheck_toggled' : self.on_ColorAllPagesCheck_toggled,
					'on_PreviewLayout_size_allocate' : self.on_PreviewLayout_size_allocate}
		self.gladeTree.signal_autoconnect(signals)
		
		if state.get_state('show_toolbar', True) == False:
			self.gladeTree.get_widget('ShowToolbarMenuItem').set_active(False)
			self.toolbar.hide()
		
		if state.get_state('show_thumbnails', True) == False:
			self.gladeTree.get_widget('ShowThumbnailsMenuItem').set_active(False)
			self.thumbnailsScrolledWindow.hide()
		
		if state.get_state('show_statusbar', True) == False:
			self.gladeTree.get_widget('ShowStatusbarMenuItem').set_active(False)
			self.statusbar.hide()
		
		self.scanWindow.show()
		
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

	def error_box(self, parent, text):
		'''Utility function to display simple error dialog.'''
		self.errorDialog.set_transient_for(parent)
		self.errorLabel.set_markup(text)
		self.errorDialog.run()
		self.errorDialog.hide()
		
	# Window destruction signal handlers
		
	def on_ScanWindow_destroy(self, object):
		self.app.quit()
		
	def on_AdjustColorsWindow_delete_event(self, widget, event):
		self.app.adjust_colors_close()
		
	# Menu signal handlers
		
	def on_ScanMenuItem_activate(self, menuItem):
		self.app.scan_page()
		
	def on_SaveAsMenuItem_activate(self, menuItem):
		self.app.save_as()
		
	def on_QuitMenuItem_activate(self, menuItem):
		self.app.quit()
		
	def on_DeleteMenuItem_activate(self, menuItem):
		self.app.delete_selected_page()
		
	def on_InsertScanMenuItem_activate(self, menuItem):
		self.app.insert_scan()
		
	def on_PreferencesMenuItem_activate(self, menuItem):
		self.app.show_preferences()
		
	def on_ShowToolbarMenuItem_toggled(self, checkMenuItem):
		self.app.toggle_toolbar(checkMenuItem)
		
	def on_ShowStatusBarMenuItem_toggled(self, checkMenuItem):
		self.app.toggle_statusbar(checkMenuItem)
		
	def on_ShowThumbnailsMenuItem_toggled(self, checkMenuItem):
		self.app.toggle_thumbnails(checkMenuItem)
		
	def on_ZoomInMenuItem_activate(self, menuItem):
		self.app.zoom_in()
		
	def on_ZoomOutMenuItem_activate(self, menuItem):
		self.app.zoom_out()
		
	def on_ZoomOneToOneMenuItem_activate(self, menuItem):
		self.app.zoom_one_to_one()
		
	def on_ZoomBestFitMenuItem_activate(self, menuItem):
		self.app.zoom_best_fit()
		
	def on_RotateCounterClockMenuItem_activate(self, menuItem):
		self.app.rotate_counter_clockwise()
		
	def on_RotateClockMenuItem_activate(self, menuItem):
		self.app.rotate_clockwise()
		
	def on_AdjustColorsMenuItem_toggled(self, checkMenuItem):
		self.app.adjust_colors_toggle(checkMenuItem)
		pass
		
	def on_GoFirstMenuItem_activate(self, menuItem):
		self.app.goto_first_page()
		
	def on_GoPreviousMenuItem_activate(self, menuItem):
		self.app.goto_previous_page()
		
	def on_GoNextMenuItem_activate(self, menuItem):
		self.app.goto_next_page()
		
	def on_GoLastMenuItem_activate(self, menuItem):
		self.app.goto_last_page()
		
	def on_AboutMenuItem_activate(self, menuItem):
		self.app.show_about()
		
	# Toolbar signal handlers
		
	def on_ScanButton_clicked(self, button):
		self.app.scan_page()
		
	def on_SaveAsButton_clicked(self, button):
		self.app.save_as()
		
	def on_ZoomInButton_clicked(self, button):
		self.app.zoom_in()
		
	def on_ZoomOutButton_clicked(self, button):
		self.app.zoom_out()
		
	def on_ZoomOneToOneButton_clicked(self, button):
		self.app.zoom_one_to_one()
		
	def on_ZoomBestFitButton_clicked(self, button):
		self.app.zoom_best_fit()
		
	def on_RotateCounterClockButton_clicked(self, button):
		self.app.rotate_counter_clockwise()
		
	def on_RotateClockButton_clicked(self, button):
		self.app.rotate_clockwise()
		
	def on_GoFirstButton_clicked(self, button):
		self.app.goto_first_page()
		
	def on_GoPreviousButton_clicked(self, button):
		self.app.goto_previous_page()
		
	def on_GoNextButton_clicked(self, button):
		self.app.goto_next_page()
		
	def on_GoLastButton_clicked(self, button):
		self.app.goto_last_page()
		
	# Miscellaneous signal handlers
		
	def on_BrightnessScale_value_changed(self, range):
		self.app.update_brightness()
		
	def on_ContrastScale_value_changed(self, range):
		self.app.update_contrast()
		
	def on_SharpnessScale_value_changed(self, range):
		self.app.update_sharpness()
		
	def on_ColorAllPagesCheck_toggled(self, toggleButton):
		self.app.color_all_pages_toggled()
		
	def on_PreviewLayout_size_allocate(self, widget, allocation):
		self.app.preview_resized(allocation)
		
	def on_ThumbnailsListStore_row_inserted(self, treeModel, path, iter):
		self.app.thumbnail_inserted(treeModel, path, iter)
		
	def on_ThumbnailsTreeSelection_changed(self, treeSelection):
		self.app.thumbnail_selected(treeSelection)
