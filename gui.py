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

'''
This module holds the GTKGui implemenation of the NoStaples interface.
'''

# Disable pylint checks that do not apply to this module
# (since most signal handlers will violate all of them).
# pylint: disable-msg=C0111
# pylint: disable-msg=W0613
# pylint: disable-msg=C0103

import logging

import gtk
import gtk.glade
import gobject

import constants

def breaking_exception_handler(func):
    '''
    A decorator that wraps top-level UI signal handlers in a
    last-resort exception handling block.  If an exception makes it
    to the surface via any of these functions then it is
    assumed to be fatal.  The exception is logged, a message
    is presented to the user, and the application is killed.
    '''
    def proxy(*args, **kwargs):
        '''Wraps the specified function in a try block'''
        try:
            return func(*args, **kwargs)
        except Exception:
            logging.getLogger().fatal(
               'Unhandled exception.', exc_info=True)
            
            primary_markup = (
                '<b>An unhandled exception has been logged.</b>')
            
            secondary_markup = (
                'NoStaples has encountered an unexpected error and must '
                'close.  Please take a moment to file a bug report so '
                'we can prevent this from happening in the future.  '
                'Instructions can be found at http://www.etlafins.com/'
                'nostaples.')
            
            msg = gtk.MessageDialog(
                type=gtk.MESSAGE_ERROR, 
                buttons=gtk.BUTTONS_OK)
            msg.set_title('')
            msg.set_markup(primary_markup)
            msg.format_secondary_markup(secondary_markup)
            msg.run()
            msg.destroy()

            gtk.main_quit()
        
    return proxy

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
        self.widgets = {}
        
        # Main Window
        
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
            self.app.state_manager['thumbnail_size'])
        self.thumbnails_tree_view.append_column(self.thumbnails_column)
        self.thumbnails_column.pack_start(self.thumbnails_cell, True)
        self.thumbnails_column.set_attributes(self.thumbnails_cell, pixbuf=0)
        self.thumbnails_tree_view.get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self.thumbnails_tree_view.set_headers_visible(False)
        self.thumbnails_tree_view.set_property('can-focus', False)
        
        self.thumbnails_tree_view.set_reorderable(True)
        self.thumbnails_list_store.connect(
            'row-inserted', self._on_thumbnails_list_store_row_inserted)
        self.thumbnails_tree_view.get_selection().connect(
            'changed', self._on_thumbnails_tree_selection_changed)
        
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
        
        if self.app.state_manager['show_toolbar'] == False:
            self.show_toolbar_menu_item.set_active(False)
            self.toolbar.hide()
        
        if self.app.state_manager['show_thumbnails'] == False:
            self.show_thumbnails_menu_item.set_active(False)
            self.thumbnails_scrolled_window.hide()
        
        if self.app.state_manager['show_statusbar'] == False:
            self.show_statusbar_menu_item.set_active(False)
            self.statusbar.hide()
            
        # Adjustments Window
        
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
            
        setup_combobox(
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
        
        # About dialog
         
        self.about_dialog = self.glade_xml.get_widget(
            'AboutDialog')
            
        self._connect_signals()
        self.scan_window.show()
        
    def _connect_signals(self):
        '''
        Connects all the signals setup in Glade to their methods.
        '''
        signals = {'on_ScanWindow_destroy' :
                self._on_scan_window_destroy,
                'on_AdjustColorsWindow_delete_event' : 
                    self._on_adjust_colors_window_delete_event,
                'on_ScanMenuItem_activate' : 
                    self._on_scan_menu_item_activate,
                'on_SaveAsMenuItem_activate' : 
                    self._on_save_as_menu_item_activate,
                'on_QuitMenuItem_activate' : 
                    self._on_quit_menu_item_activate,
                'on_DeleteMenuItem_activate' : 
                    self._on_delete_menu_item_activate,
                'on_InsertScanMenuItem_activate' : 
                    self._on_insert_scan_menu_item_activate,
                'on_PreferencesMenuItem_activate' : 
                    self._on_preferences_menu_item_activate,
                'on_ShowToolbarMenuItem_toggled' : 
                    self._on_show_toolbar_menu_item_toggled,
                'on_ShowStatusBarMenuItem_toggled' : 
                    self._on_show_statusbar_menu_item_toggled,
                'on_ShowThumbnailsMenuItem_toggled' : 
                    self._on_show_thumbnails_menu_item_toggled,
                'on_ZoomInMenuItem_activate' : 
                    self._on_zoom_in_menu_item_activate,
                'on_ZoomOutMenuItem_activate' : 
                    self._on_zoom_out_menu_item_activate,
                'on_ZoomOneToOneMenuItem_activate' : 
                    self._on_zoom_one_to_one_menu_item_activate,
                'on_ZoomBestFitMenuItem_activate' : 
                    self._on_zoom_best_fit_menu_item_activate,
                'on_RotateCounterClockMenuItem_activate' : 
                    self._on_rotate_counter_clock_menu_item_activate,
                'on_RotateClockMenuItem_activate' : 
                    self._on_rotate_clock_menu_item_activate,
                'on_AdjustColorsMenuItem_toggled' : 
                    self._on_adjust_colors_menu_item_toggled,
                'on_GoFirstMenuItem_activate' :
                    self._on_go_first_menu_item_activate,
                'on_GoPreviousMenuItem_activate' : 
                    self._on_go_previous_menu_item_activate,
                'on_GoNextMenuItem_activate' : 
                    self._on_go_next_menu_item_activate,
                'on_GoLastMenuItem_activate' : 
                    self._on_go_last_menu_item_activate,
                'on_AboutMenuItem_activate' : 
                    self._on_about_menu_item_activate,
                'on_ScanButton_clicked' :
                    self._on_scan_button_clicked,
                'on_SaveAsButton_clicked' :
                    self._on_save_as_button_clicked,
                'on_ZoomInButton_clicked' : 
                    self._on_zoom_in_button_clicked,
                'on_ZoomOutButton_clicked' : 
                    self._on_zoom_out_button_clicked,
                'on_ZoomOneToOneButton_clicked' : 
                    self._on_zoom_one_to_one_button_clicked,
                'on_ZoomBestFitButton_clicked' :
                    self._on_zoom_best_fit_button_clicked,
                'on_RotateCounterClockButton_clicked' :
                    self._on_rotate_counter_clock_button_clicked,
                'on_RotateClockButton_clicked' :
                    self._on_rotate_clock_button_clicked,
                'on_GoFirstButton_clicked' :
                    self._on_go_first_button_clicked,
                'on_GoPreviousButton_clicked' :
                    self._on_go_previous_button_clicked,
                'on_GoNextButton_clicked' :
                    self._on_go_next_button_clicked,
                'on_GoLastButton_clicked' :
                    self._on_go_last_button_clicked,
                'on_BrightnessScale_value_changed' :
                    self._on_brightness_scale_value_changed,        
                'on_ContrastScale_value_changed' :
                    self._on_contrast_scale_value_changed,        
                'on_SharpnessScale_value_changed' :
                    self._on_sharpness_scale_value_changed,
                'on_ColorAllPagesCheck_toggled' :
                    self._on_color_all_pages_check_toggled,
                'on_TitleEntry_activate' :
                    self._on_title_entry_activate,
                'on_AuthorEntry_activate' :
                    self._on_author_entry_activate,
                'on_KeywordsEntry_activate' :
                    self._on_keywords_entry_activate,
                'on_PreviewLayout_size_allocate' :
                    self._on_preview_layout_size_allocate,
                'on_PreviewLayout_button_press_event' :
                    self._on_preview_layout_button_press_event,
                'on_PreviewLayout_button_release_event' :
                    self._on_preview_layout_button_release_event,
                'on_PreviewLayout_motion_notify_event' : 
                    self._on_preview_layout_motion_notify_event,
                'on_PreviewLayout_scroll_event' :
                    self._on_preview_layout_scroll_event}
        
        self.glade_xml.signal_autoconnect(signals)
    
    def error_box(self, parent, primary_markup, secondary_markup=None):
        '''
        Utility function to display simple error dialog.
        '''        
        msg = gtk.MessageDialog(
            parent=parent,
            type=gtk.MESSAGE_ERROR, 
            buttons=gtk.BUTTONS_OK)
        msg.set_title('')
        msg.set_markup(primary_markup)
        
        if secondary_markup:
            msg.format_secondary_markup(secondary_markup)
            
        msg.run()
        msg.destroy()
        
    # Sensitivity functions
    
    def set_file_controls_sensitive(self, sensitive):
        '''
        Enables or disables all gui widgets related to saving.
        '''
        self.save_as_menu_item.set_sensitive(sensitive)
        self.save_as_button.set_sensitive(sensitive)
            
    def set_scan_controls_sensitive(self, sensitive):
        '''
        Enables or disables all gui widgets related to scanning and
        setting of scanner options.
        '''
        self.scan_menu_item.set_sensitive(sensitive)
        self.insert_scan_menu_item.set_sensitive(sensitive)
        self.scan_button.set_sensitive(sensitive)
            
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
        '''
        Enables or disables all gui widgets related to zooming.
        '''
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
        '''
        Enables or disables all gui widgets related to navigation.
        '''
        self.go_first_menu_item.set_sensitive(sensitive)
        self.go_previous_menu_item.set_sensitive(sensitive)
        self.go_next_menu_item.set_sensitive(sensitive)
        self.go_last_menu_item.set_sensitive(sensitive)
        self.go_first_button.set_sensitive(sensitive)
        self.go_previous_button.set_sensitive(sensitive)
        self.go_next_button.set_sensitive(sensitive)
        self.go_last_button.set_sensitive(sensitive)
    
    # Window destruction signal handlers
    
    @breaking_exception_handler
    def _on_scan_window_destroy(self, window):
        raise Exception
        self.app.quit()
        
    @breaking_exception_handler
    def _on_adjust_colors_window_delete_event(self, widget, event):
        self.adjust_colors_window.hide()
        self.adjust_colors_menu_item.set_active(False)
        return True
        
    # Menu signal handlers
            
    @breaking_exception_handler
    def _on_scan_menu_item_activate(self, menu_item):
        self.app.scan_page()
        
    @breaking_exception_handler
    def _on_save_as_menu_item_activate(self, menu_item):
        self.app.save_as()
        
    @breaking_exception_handler
    def _on_quit_menu_item_activate(self, menu_item):
        self.app.quit()
        
    @breaking_exception_handler
    def _on_delete_menu_item_activate(self, menu_item):
        self.app.delete_selected_page()
        
    @breaking_exception_handler
    def _on_insert_scan_menu_item_activate(self, menu_item):
        self.app.insert_scan()
        
    @breaking_exception_handler
    def _on_preferences_menu_item_activate(self, menu_item):
        self.app.show_preferences()
        
    @breaking_exception_handler
    def _on_show_toolbar_menu_item_toggled(self, check_menu_item):
        self.app.state_manager['show_toolbar'] = \
            check_menu_item.get_active()
        self.app.update_toolbar_visibility()
        
    @breaking_exception_handler
    def _on_show_statusbar_menu_item_toggled(self, check_menu_item):
        self.app.state_manager['show_statusbar'] = \
            check_menu_item.get_active()
        self.app.update_statusbar_visibility()
        
    @breaking_exception_handler
    def _on_show_thumbnails_menu_item_toggled(self, check_menu_item):
        self.app.state_manager['show_thumbnails'] = \
            check_menu_item.get_active()
        self.app.update_thumbnails_visibility()
        
    @breaking_exception_handler
    def _on_zoom_in_menu_item_activate(self, menu_item):
        self.app.zoom_in()
        
    @breaking_exception_handler
    def _on_zoom_out_menu_item_activate(self, menu_item):
        self.app.zoom_out()
        
    @breaking_exception_handler
    def _on_zoom_one_to_one_menu_item_activate(self, menu_item):
        self.app.zoom_one_to_one()
        
    @breaking_exception_handler
    def _on_zoom_best_fit_menu_item_activate(self, menu_item):
        self.app.zoom_best_fit()
        
    @breaking_exception_handler
    def _on_rotate_counter_clock_menu_item_activate(self, menu_item):
        self.app.rotate_counter_clockwise()
        
    @breaking_exception_handler
    def _on_rotate_clock_menu_item_activate(self, menu_item):
        self.app.rotate_clockwise()
        
    @breaking_exception_handler
    def _on_adjust_colors_menu_item_toggled(self, check_menu_item):
        self.app.adjust_colors_toggle()
        
    @breaking_exception_handler
    def _on_go_first_menu_item_activate(self, menu_item):
        self.app.goto_first_page()
        
    @breaking_exception_handler
    def _on_go_previous_menu_item_activate(self, menu_item):
        self.app.goto_previous_page()
        
    @breaking_exception_handler
    def _on_go_next_menu_item_activate(self, menu_item):
        self.app.goto_next_page()
        
    @breaking_exception_handler
    def _on_go_last_menu_item_activate(self, menu_item):
        self.app.goto_last_page()
        
    @breaking_exception_handler
    def _on_about_menu_item_activate(self, menu_item):
        self.app.show_about()
        
    # Toolbar signal handlers
        
    @breaking_exception_handler
    def _on_scan_button_clicked(self, button):
        self.app.scan_page()
        
    @breaking_exception_handler
    def _on_save_as_button_clicked(self, button):
        self.app.save_as()
        
    @breaking_exception_handler
    def _on_zoom_in_button_clicked(self, button):
        self.app.zoom_in()
        
    @breaking_exception_handler
    def _on_zoom_out_button_clicked(self, button):
        self.app.zoom_out()
        
    @breaking_exception_handler
    def _on_zoom_one_to_one_button_clicked(self, button):
        self.app.zoom_one_to_one()
        
    @breaking_exception_handler
    def _on_zoom_best_fit_button_clicked(self, button):
        self.app.zoom_best_fit()
        
    @breaking_exception_handler
    def _on_rotate_counter_clock_button_clicked(self, button):
        self.app.rotate_counter_clockwise()
        
    @breaking_exception_handler
    def _on_rotate_clock_button_clicked(self, button):
        self.app.rotate_clockwise()
        
    @breaking_exception_handler
    def _on_go_first_button_clicked(self, button):
        self.app.goto_first_page()
        
    @breaking_exception_handler
    def _on_go_previous_button_clicked(self, button):
        self.app.goto_previous_page()
        
    @breaking_exception_handler
    def _on_go_next_button_clicked(self, button):
        self.app.goto_next_page()
        
    @breaking_exception_handler
    def _on_go_last_button_clicked(self, button):
        self.app.goto_last_page()
        
    # Miscellaneous signal handlers
        
    @breaking_exception_handler
    def _on_brightness_scale_value_changed(self, scale_range):
        self.app.update_brightness()
        
    @breaking_exception_handler
    def _on_contrast_scale_value_changed(self, scale_range):
        self.app.update_contrast()
        
    @breaking_exception_handler
    def _on_sharpness_scale_value_changed(self, scale_range):
        self.app.update_sharpness()
        
    @breaking_exception_handler
    def _on_color_all_pages_check_toggled(self, toggle_button):
        self.app.color_all_pages_toggled()
        
    @breaking_exception_handler
    def _on_title_entry_activate(self, widget):
        #~ self.metadata_dialog.response(1)
        self.pdf_metadata_apply_button.clicked()
        
    @breaking_exception_handler
    def _on_author_entry_activate(self, widget):
        #~ self.metadata_dialog.response(1)
        self.pdf_metadata_apply_button.clicked()
        
    @breaking_exception_handler
    def _on_keywords_entry_activate(self, widget):
        #~ self.metadata_dialog.response(1)
        self.pdf_metadata_apply_button.clicked()
        
    @breaking_exception_handler
    def _on_preview_layout_size_allocate(self, widget, allocation):
        self.app.preview_resized(allocation)
        
    @breaking_exception_handler
    def _on_preview_layout_button_press_event(self, widget, event):
        self.app.preview_button_pressed(event)
        
    @breaking_exception_handler
    def _on_preview_layout_button_release_event(self, widget, event):
        self.app.preview_button_released(event)
        
    @breaking_exception_handler
    def _on_preview_layout_motion_notify_event(self, widget, event):
        self.app.preview_mouse_moved(event)
        
    @breaking_exception_handler
    def _on_preview_layout_scroll_event(self, widget, event):
        self.app.preview_scrolled(event)
        
    @breaking_exception_handler
    def _on_thumbnails_list_store_row_inserted(self, tree_model, path, tree_iter):
        self.app.thumbnail_inserted(tree_model, path, tree_iter)
        
    @breaking_exception_handler
    def _on_thumbnails_tree_selection_changed(self, tree_selection):
        self.app.thumbnail_selected(tree_selection)
        
# Utility functions

def setup_combobox(combobox, item_list, selection):
    '''
    A short-cut for setting up simple comboboxes.
    '''
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
    
def read_combobox(combobox):
    '''
    A short-cut for reading from simple comboboxes.
    '''
    liststore = combobox.get_model()
    active = combobox.get_active()
    
    if active < 0:
        return None
        
    return liststore[active][0]
