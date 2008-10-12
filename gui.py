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

class GtkGUI():
    '''
    A wrapper class to keep the details of the gui (esp. signal handlers) 
    away from the main application code.
    '''
    
    def __init__(self, app, glade_file):
        '''
        Initializes the gui from a glade xml file and sets up controls that could 
        not be configured in the glade editor.
        '''
        self.app = app
        
        self.glade_file = glade_file
        self.glade_xml = gtk.glade.XML(self.glade_file)
        
        # Main window
        
        self.scan_window = self.glade_xml.get_widget('ScanWindow')
        self.scan_window.set_property('allow-shrink', True)
        
        self.scan_menu_item = self.glade_xml.get_widget(
            'ScanMenuItem')
        self.save_as_menu_item = self.glade_xml.get_widget(
            'SaveAsMenuItem')
        self.quit_menu_item = self.glade_xml.get_widget(
            'QuitMenuItem')
        self.delete_menu_item = self.glade_xml.get_widget(
            'DeleteMenuItem')
        self.insert_scan_menu_item = self.glade_xml.get_widget(
            'InsertScanMenuItem')
        self.preferences_menu_item = self.glade_xml.get_widget(
            'PreferencesMenuItem')
        self.show_toolbar_menu_item = self.glade_xml.get_widget(
            'ShowToolbarMenuItem')
        self.show_statusbar_menu_item = self.glade_xml.get_widget(
            'ShowStatusbarMenuItem')
        self.show_thumbnails_menu_item = self.glade_xml.get_widget(
            'ShowThumbnailsMenuItem')
        self.zoom_in_menu_item = self.glade_xml.get_widget(
            'ZoomInMenuItem')
        self.zoom_out_menu_item = self.glade_xml.get_widget(
            'ZoomOutMenuItem')
        self.zoom_one_to_one_menu_item = self.glade_xml.get_widget(
            'ZoomOneToOneMenuItem')
        self.zoom_best_fit_menu_item = self.glade_xml.get_widget(
            'ZoomBestFitMenuItem')
        self.rotate_counter_clock_menu_item = self.glade_xml.get_widget(
            'RotateCounterClockMenuItem')
        self.rotate_clock_menu_item = self.glade_xml.get_widget(
            'RotateClockMenuItem')
        self.rotate_all_pages_menu_item = self.glade_xml.get_widget(
            'RotateAllPagesMenuItem')
        self.adjust_colors_menu_item = self.glade_xml.get_widget(
            'AdjustColorsMenuItem')
        self.scanner_sub_menu = self.glade_xml.get_widget(
            'ScannerSubMenu')
        self.scan_mode_sub_menu = self.glade_xml.get_widget(
            'ScanModeSubMenu')
        self.scan_resolution_sub_menu = self.glade_xml.get_widget(
            'ScanResolutionSubMenu')
        self.go_first_menu_item = self.glade_xml.get_widget(
            'GoFirstMenuItem')
        self.go_previous_menu_item = self.glade_xml.get_widget(
            'GoPreviousMenuItem')
        self.go_next_menu_item = self.glade_xml.get_widget(
            'GoNextMenuItem')
        self.go_last_menu_item = self.glade_xml.get_widget(
            'GoLastMenuItem')
        self.about_menu_item = self.glade_xml.get_widget(
            'AboutMenuItem')
        
        self.toolbar = self.glade_xml.get_widget(
            'MainToolbar')    
        self.scan_button = self.glade_xml.get_widget(
            'ScanButton')
        self.save_as_button = self.glade_xml.get_widget(
            'SaveAsButton')
        self.zoom_in_button = self.glade_xml.get_widget(
            'ZoomInButton')
        self.zoom_out_button = self.glade_xml.get_widget(
            'ZoomOutButton')
        self.zoom_one_to_one_button = self.glade_xml.get_widget(
            'ZoomOneToOneButton')
        self.zoom_best_fit_button = self.glade_xml.get_widget(
            'ZoomBestFitButton')
        self.rotate_counter_clock_button = self.glade_xml.get_widget(
            'RotateCounterClockButton')
        self.rotate_clock_button = self.glade_xml.get_widget(
            'RotateClockButton')
        self.go_first_button = self.glade_xml.get_widget(
            'GoFirstButton')
        self.go_previous_button = self.glade_xml.get_widget(
            'GoPreviousButton')
        self.go_next_button = self.glade_xml.get_widget(
            'GoNextButton')
        self.go_last_button = self.glade_xml.get_widget(
            'GoLastButton')

        self.thumbnails_scrolled_window = self.glade_xml.get_widget(
            'ThumbnailsScrolledWindow')
        self.thumbnails_list_store = gtk.ListStore(gtk.gdk.Pixbuf)
        self.thumbnails_tree_view = gtk.TreeView(self.thumbnails_list_store)
        self.thumbnails_column = gtk.TreeViewColumn(None)
        self.thumbnails_cell = gtk.CellRendererPixbuf()
        self.thumbnails_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.thumbnails_column.set_fixed_width(
            self.app.state_engine.get_state('thumbnail_size'))
        self.thumbnails_tree_view.append_column(self.thumbnails_column)
        self.thumbnails_column.pack_start(self.thumbnails_cell, True)
        self.thumbnails_column.set_attributes(self.thumbnails_cell, pixbuf=0)
        self.thumbnails_tree_view.get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self.thumbnails_tree_view.set_headers_visible(False)
        self.thumbnails_tree_view.set_property('can-focus', False)
        
        self.thumbnails_tree_view.set_reorderable(True)
        self.thumbnails_list_store.connect(
            'row-inserted', self.on_thumbnails_list_store_row_inserted)
        self.thumbnails_tree_view.get_selection().connect(
            'changed', self.on_thumbnails_tree_selection_changed)
        
        self.thumbnails_scrolled_window.add(self.thumbnails_tree_view)
        self.thumbnails_scrolled_window.show_all()
        
        self.preview_layout = self.glade_xml.get_widget(
            'PreviewLayout')
        self.preview_horizontal_scroll = self.glade_xml.get_widget(
            'PreviewHScroll')
        self.preview_vertical_scroll = self.glade_xml.get_widget(
            'PreviewVScroll')
        self.preview_horizontal_scroll.set_adjustment(
            self.preview_layout.get_hadjustment())
        self.preview_vertical_scroll.set_adjustment(
            self.preview_layout.get_vadjustment())
        
        self.preview_image_display = gtk.Image()
        self.preview_layout.add(self.preview_image_display)
        self.preview_layout.modify_bg(
            gtk.STATE_NORMAL, 
            gtk.gdk.colormap_get_system().alloc_color(
                gtk.gdk.Color(0, 0, 0), False, True))
        self.preview_image_display.show()

        self.statusbar = self.glade_xml.get_widget(
            'ScanStatusBar')
        self.statusbar.push(constants.STATUSBAR_BASE_CONTEXT_ID, 'Ready')
        
        if self.app.state_engine.get_state('show_toolbar') == False:
            self.show_toolbar_menu_item.set_active(False)
            self.toolbar.hide()
        
        if self.app.state_engine.get_state('show_thumbnails') == False:
            self.show_thumbnails_menu_item.set_active(False)
            self.thumbnails_scrolled_window.hide()
        
        if self.app.state_engine.get_state('show_statusbar') == False:
            self.show_statusbar_menu_item.set_active(False)
            self.statusbar.hide()
        
        # Adjust colors window
        
        self.adjust_colors_window = self.glade_xml.get_widget(
            'AdjustColorsWindow')
        
        self.brightness_scale = self.glade_xml.get_widget(
            'BrightnessScale')
        self.contrast_scale = self.glade_xml.get_widget(
            'ContrastScale')
        self.sharpness_scale = self.glade_xml.get_widget(
            'SharpnessScale')
        self.color_all_pages_check = self.glade_xml.get_widget(
            'ColorAllPagesCheck')

        # Preferences dialog
        
        self.preferences_dialog = self.glade_xml.get_widget(
            'PreferencesDialog')
        self.preview_mode_combo_box = self.glade_xml.get_widget(
            'PreviewModeComboBox')
        self.setup_combobox(
            self.preview_mode_combo_box, 
            ['Nearest (Fastest)',
                'Bilinear', 
                'Bicubic', 
                'Antialias (Clearest)'], 
            'Antialias (Clearest)')
        
        # PDF Metadata dialog
        
        self.metadata_dialog = self.glade_xml.get_widget(
            'MetadataDialog')
        
        self.title_entry = self.glade_xml.get_widget(
            'TitleEntry')
        self.author_entry = self.glade_xml.get_widget(
            'AuthorEntry')
        self.keywords_entry = self.glade_xml.get_widget(
            'KeywordsEntry')
        self.pdf_metadata_apply_button = self.glade_xml.get_widget(
            'PdfMetadataApplyButton')
        
        # Save dialog
        
        self.save_dialog = self.glade_xml.get_widget(
            'SaveDialog')
        
        # Error dialog
        
        self.error_dialog = self.glade_xml.get_widget(
            'ErrorDialog')
        self.error_label = self.glade_xml.get_widget(
            'ErrorLabel')
        
        # About dialog
        
        self.about_dialog = self.glade_xml.get_widget(
            'AboutDialog')
        
        # Connect signals and show main window

        signals = {'on_ScanWindow_destroy' :
                            self.on_scan_window_destroy,
                        'on_AdjustColorsWindow_delete_event' : 
                            self.on_adjust_colors_window_delete_event,
                        'on_ScanMenuItem_activate' : 
                            self.on_scan_menu_item_activate,
                        'on_SaveAsMenuItem_activate' : 
                            self.on_save_as_menu_item_activate,
                        'on_QuitMenuItem_activate' : 
                            self.on_quit_menu_item_activate,
                        'on_DeleteMenuItem_activate' : 
                            self.on_delete_menu_item_activate,
                        'on_InsertScanMenuItem_activate' : 
                            self.on_insert_scan_menu_item_activate,
                        'on_PreferencesMenuItem_activate' : 
                            self.on_preferences_menu_item_activate,
                        'on_ShowToolbarMenuItem_toggled' : 
                            self.on_show_toolbar_menu_item_toggled,
                        'on_ShowStatusBarMenuItem_toggled' : 
                            self.on_show_statusbar_menu_item_toggled,
                        'on_ShowThumbnailsMenuItem_toggled' : 
                            self.on_show_thumbnails_menu_item_toggled,
                        'on_ZoomInMenuItem_activate' : 
                            self.on_zoom_in_menu_item_activate,
                        'on_ZoomOutMenuItem_activate' : 
                            self.on_zoom_out_menu_item_activate,
                        'on_ZoomOneToOneMenuItem_activate' : 
                            self.on_zoom_one_to_one_menu_item_activate,
                        'on_ZoomBestFitMenuItem_activate' : 
                            self.on_zoom_best_fit_menu_item_activate,
                        'on_RotateCounterClockMenuItem_activate' : 
                            self.on_rotate_counter_clock_menu_item_activate,
                        'on_RotateClockMenuItem_activate' : 
                            self.on_rotate_clock_menu_item_activate,
                        'on_AdjustColorsMenuItem_toggled' : 
                            self.on_adjust_colors_menu_item_toggled,
                        'on_GoFirstMenuItem_activate' :
                            self.on_go_first_menu_item_activate,
                        'on_GoPreviousMenuItem_activate' : 
                            self.on_go_previous_menu_item_activate,
                        'on_GoNextMenuItem_activate' : 
                            self.on_go_next_menu_item_activate,
                        'on_GoLastMenuItem_activate' : 
                            self.on_go_last_menu_item_activate,
                        'on_AboutMenuItem_activate' : 
                            self.on_about_menu_item_activate,
                        'on_ScanButton_clicked' :
                            self.on_scan_button_clicked,
                        'on_SaveAsButton_clicked' :
                            self.on_save_as_button_clicked,
                        'on_ZoomInButton_clicked' : 
                            self.on_zoom_in_button_clicked,
                        'on_ZoomOutButton_clicked' : 
                            self.on_zoom_out_button_clicked,
                        'on_ZoomOneToOneButton_clicked' : 
                            self.on_zoom_one_to_one_button_clicked,
                        'on_ZoomBestFitButton_clicked' :
                            self.on_zoom_best_fit_button_clicked,
                        'on_RotateCounterClockButton_clicked' :
                            self.on_rotate_counter_clock_button_clicked,
                        'on_RotateClockButton_clicked' :
                            self.on_rotate_clock_button_clicked,
                        'on_GoFirstButton_clicked' :
                            self.on_go_first_button_clicked,
                        'on_GoPreviousButton_clicked' :
                            self.on_go_previous_button_clicked,
                        'on_GoNextButton_clicked' :
                            self.on_go_next_button_clicked,
                        'on_GoLastButton_clicked' :
                            self.on_go_last_button_clicked,
                        'on_BrightnessScale_value_changed' :
                            self.on_brightness_scale_value_changed,        
                        'on_ContrastScale_value_changed' :
                            self.on_contrast_scale_value_changed,        
                        'on_SharpnessScale_value_changed' :
                            self.on_sharpness_scale_value_changed,
                        'on_ColorAllPagesCheck_toggled' :
                            self.on_color_all_pages_check_toggled,
                        'on_TitleEntry_activate' :
                            self.on_title_entry_activate,
                        'on_AuthorEntry_activate' :
                            self.on_author_entry_activate,
                        'on_KeywordsEntry_activate' :
                            self.on_keywords_entry_activate,
                        'on_PreviewLayout_size_allocate' :
                            self.on_preview_layout_size_allocate,
                        'on_PreviewLayout_button_press_event' :
                            self.on_preview_layout_button_press_event,
                        'on_PreviewLayout_button_release_event' :
                            self.on_preview_layout_button_release_event,
                        'on_PreviewLayout_motion_notify_event' : 
                            self.on_preview_layout_motion_notify_event,
                        'on_PreviewLayout_scroll_event' :
                            self.on_preview_layout_scroll_event}
        
        self.glade_xml.signal_autoconnect(signals)
        
        self.scan_window.show()
        
    # Utility functions
        
    def setup_combobox(self, combobox, item_list, selection):
        '''A short-cut for setting up simple comboboxes.'''
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        combobox.clear()
        combobox.set_model(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)  

        for item in item_list:
            liststore.append([item])
            
        try:
            index = item_list.index(selection)
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
        self.error_dialog.set_transient_for(parent)
        self.error_label.set_markup(text)
        self.error_dialog.run()
        self.error_dialog.hide()
        
    # Sensitivity functions
    
    def set_file_controls_sensitive(self, sensitive):
        '''
        Enables or disables all gui widgets related to scanning, saving, 
        or manipulation of pages.
        '''
        self.save_as_menu_item.set_sensitive(sensitive)
        self.save_as_button.set_sensitive(sensitive)
            
    def set_scan_controls_sensitive(self, sensitive):
        self.scan_menu_item.set_sensitive(sensitive)
        self.insert_scan_menu_item.set_sensitive(sensitive)
        self.scan_button.set_sensitive(sensitive)
        
        for child in self.scanner_sub_menu.get_children():
            child.set_sensitive(sensitive)
            
        for child in self.scan_mode_sub_menu.get_children():
            child.set_sensitive(sensitive)
            
        for child in self.scan_resolution_sub_menu.get_children():
            child.set_sensitive(sensitive)
            
    def set_delete_controls_sensitive(self, sensitive):
        '''
        Enables or disables all gui widgets related to deleting or reordering 
        pages.
        '''
        self.delete_menu_item.set_sensitive(sensitive)
    
    def set_zoom_controls_sensitive(self, sensitive):
        '''Enables or disables all gui widgets related to zooming.'''
        self.zoom_in_menu_item.set_sensitive(sensitive)
        self.zoom_out_menu_item.set_sensitive(sensitive)
        self.zoom_one_to_one_menu_item.set_sensitive(sensitive)
        self.zoom_best_fit_menu_item.set_sensitive(sensitive)
        self.zoom_in_button.set_sensitive(sensitive)
        self.zoom_out_button.set_sensitive(sensitive)
        self.zoom_one_to_one_button.set_sensitive(sensitive)
        self.zoom_best_fit_button.set_sensitive(sensitive)
        
    def set_adjustment_controls_sensitive(self, sensitive):
        '''
        Enables or disables all gui widgets related to making adjustments to 
        the current page.
        '''
        self.rotate_counter_clock_menu_item.set_sensitive(sensitive)
        self.rotate_clock_menu_item.set_sensitive(sensitive)
        self.rotate_all_pages_menu_item.set_sensitive(sensitive)
        self.rotate_counter_clock_button.set_sensitive(sensitive)
        self.rotate_clock_button.set_sensitive(sensitive)
        
        self.brightness_scale.set_sensitive(sensitive)
        self.contrast_scale.set_sensitive(sensitive)
        self.sharpness_scale.set_sensitive(sensitive)
        self.color_all_pages_check.set_sensitive(sensitive)

    def set_navigation_controls_sensitive(self, sensitive):
        '''Enables or disables all gui widgets related to navigation.'''
        self.go_first_menu_item.set_sensitive(sensitive)
        self.go_previous_menu_item.set_sensitive(sensitive)
        self.go_next_menu_item.set_sensitive(sensitive)
        self.go_last_menu_item.set_sensitive(sensitive)
        self.go_first_button.set_sensitive(sensitive)
        self.go_previous_button.set_sensitive(sensitive)
        self.go_next_button.set_sensitive(sensitive)
        self.go_last_button.set_sensitive(sensitive)
        
    # Window destruction signal handlers
        
    def on_scan_window_destroy(self, window):
        self.app.quit()
        
    def on_adjust_colors_window_delete_event(self, widget, event):
        self.adjust_colors_window.hide()
        self.adjust_colors_menu_item.set_active(False)
        return True
        
    # Menu signal handlers
        
    def on_scan_menu_item_activate(self, menu_item):
        self.app.scan_page()
        
    def on_save_as_menu_item_activate(self, menu_item):
        self.app.save_as()
        
    def on_quit_menu_item_activate(self, menu_item):
        self.app.quit()
        
    def on_delete_menu_item_activate(self, menu_item):
        self.app.delete_selected_page()
        
    def on_insert_scan_menu_item_activate(self, menu_item):
        self.app.insert_scan()
        
    def on_preferences_menu_item_activate(self, menu_item):
        self.app.show_preferences()
        
    def on_show_toolbar_menu_item_toggled(self, checkMenuItem):
        self.app.state_engine.set_state(
            'show_toolbar', checkMenuItem.get_active())
        
    def on_show_statusbar_menu_item_toggled(self, checkMenuItem):
        self.app.state_engine.set_state(
            'show_statusbar', checkMenuItem.get_active())
        
    def on_show_thumbnails_menu_item_toggled(self, checkMenuItem):
        self.app.state_engine.set_state(
            'show_thumbnails', checkMenuItem.get_active())
        
    def on_zoom_in_menu_item_activate(self, menu_item):
        self.app.zoom_in()
        
    def on_zoom_out_menu_item_activate(self, menu_item):
        self.app.zoom_out()
        
    def on_zoom_one_to_one_menu_item_activate(self, menu_item):
        self.app.zoom_one_to_one()
        
    def on_zoom_best_fit_menu_item_activate(self, menu_item):
        self.app.zoom_best_fit()
        
    def on_rotate_counter_clock_menu_item_activate(self, menu_item):
        self.app.rotate_counter_clockwise()
        
    def on_rotate_clock_menu_item_activate(self, menu_item):
        self.app.rotate_clockwise()
        
    def on_adjust_colors_menu_item_toggled(self, checkMenuItem):
        self.app.adjust_colors_toggle()
        
    def on_go_first_menu_item_activate(self, menu_item):
        self.app.goto_first_page()
        
    def on_go_previous_menu_item_activate(self, menu_item):
        self.app.goto_previous_page()
        
    def on_go_next_menu_item_activate(self, menu_item):
        self.app.goto_next_page()
        
    def on_go_last_menu_item_activate(self, menu_item):
        self.app.goto_last_page()
        
    def on_about_menu_item_activate(self, menu_item):
        self.app.show_about()
        
    # Toolbar signal handlers
        
    def on_scan_button_clicked(self, button):
        self.app.scan_page()
        
    def on_save_as_button_clicked(self, button):
        self.app.save_as()
        
    def on_zoom_in_button_clicked(self, button):
        self.app.zoom_in()
        
    def on_zoom_out_button_clicked(self, button):
        self.app.zoom_out()
        
    def on_zoom_one_to_one_button_clicked(self, button):
        self.app.zoom_one_to_one()
        
    def on_zoom_best_fit_button_clicked(self, button):
        self.app.zoom_best_fit()
        
    def on_rotate_counter_clock_button_clicked(self, button):
        self.app.rotate_counter_clockwise()
        
    def on_rotate_clock_button_clicked(self, button):
        self.app.rotate_clockwise()
        
    def on_go_first_button_clicked(self, button):
        self.app.goto_first_page()
        
    def on_go_previous_button_clicked(self, button):
        self.app.goto_previous_page()
        
    def on_go_next_button_clicked(self, button):
        self.app.goto_next_page()
        
    def on_go_last_button_clicked(self, button):
        self.app.goto_last_page()
        
    # Miscellaneous signal handlers
        
    def on_brightness_scale_value_changed(self, scale_range):
        self.app.update_brightness()
        
    def on_contrast_scale_value_changed(self, scale_range):
        self.app.update_contrast()
        
    def on_sharpness_scale_value_changed(self, scale_range):
        self.app.update_sharpness()
        
    def on_color_all_pages_check_toggled(self, toggle_button):
        self.app.color_all_pages_toggled()
        
    def on_title_entry_activate(self, widget):
        #~ self.metadata_dialog.response(1)
        self.pdf_metadata_apply_button.clicked()
        
    def on_author_entry_activate(self, widget):
        #~ self.metadata_dialog.response(1)
        self.pdf_metadata_apply_button.clicked()
        
    def on_keywords_entry_activate(self, widget):
        #~ self.metadata_dialog.response(1)
        self.pdf_metadata_apply_button.clicked()
        
    def on_preview_layout_size_allocate(self, widget, allocation):
        self.app.preview_resized(allocation)
        
    def on_preview_layout_button_press_event(self, widget, event):
        self.app.preview_button_pressed(event)
        
    def on_preview_layout_button_release_event(self, widget, event):
        self.app.preview_button_released(event)
        
    def on_preview_layout_motion_notify_event(self, widget, event):
        self.app.preview_mouse_moved(event)
        
    def on_preview_layout_scroll_event(self, widget, event):
        self.app.preview_scrolled(event)
        
    def on_thumbnails_list_store_row_inserted(self, tree_model, path, tree_iter):
        self.app.thumbnail_inserted(tree_model, path, tree_iter)
        
    def on_thumbnails_tree_selection_changed(self, tree_selection):
        self.app.thumbnail_selected(tree_selection)
