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

'''
This module holds all the NoStaples application functionality.  GUI handling,
state persistence, and scanning are each handled in their own modules.
'''

import logging.config
import os
import sys
import threading

import gtk
from reportlab.pdfgen.canvas import Canvas as PdfCanvas
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.units import inch as points_per_inch

import constants
import state
import page
import gui
import scanning

gtk.gdk.threads_init()

def main():
    app = NoStaples()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()

def threaded(func):
    '''Threading function decorator.'''
    def proxy(*args, **kwargs):
        '''Invokes the specified function on a new thread.'''
        new_thread = threading.Thread(
            target=func, args=args, kwargs=kwargs)
        new_thread.start()
        return new_thread
    return proxy
    
class NoStaples:
    '''
    NoStaples' main application class.
    '''
    def __init__(self):
        '''
        Sets up all application variables (including loading saved settings), 
        loads the interface via glade, connects signals, and then shows the 
        scanning window.
        '''
        logging.config.fileConfig(constants.LOGGING_CONFIG)
        logging.getLogger().debug('Application started.')
        
        self.state_manager = state.GConfStateManager()
        self._init_states()
        
        # This is a dictionary of the available scanners.
        # The keys are human readable scanner descriptions.
        # The values are sane-backend descriptors.
        self.scanner_dict = {}
        self.active_scanner = self.state_manager['active_scanner']
        
        # This is a list of Page objects.
        self.scanned_pages = []
        self.next_scan_file_index = 0
        
        self.preview_index = 0
        self.preview_pixbuf = None
        self.scaled_pixbuf = None
        self.preview_width = 0
        self.preview_height = 0
        self.preview_zoom = 1.0
        self.preview_is_best_fit = True
        
        self.preview_drag_start = (0, 0)
        self.preview_zoom_rect_color = \
            gtk.gdk.colormap_get_system().alloc_color(
                gtk.gdk.Color(65535, 0, 0), False, True)
        self.zoom_drag_start_x = 0
        self.zoom_drag_start_y = 0
        
        self.thumbnail_size = self.state_manager['thumbnail_size']
        self.thumbnail_selection = None
        self.insert_is_not_drag = False
        
        self.scan_event = threading.Event()
        self.cancel_scan_event = threading.Event()
        self.quit_event = threading.Event()
        
        self.gui = gui.GtkGUI(self, constants.GLADE_CONFIG)
        self.gui.set_file_controls_sensitive(False)
        self.gui.set_delete_controls_sensitive(False)
        self.gui.set_zoom_controls_sensitive(False)
        self.gui.set_adjustment_controls_sensitive(False)        
        self.gui.set_navigation_controls_sensitive(False)        
        
        self.update_scanner_list()
        
    def _init_states(self):
        '''
        Initializes each state that is tracked in the state engine, setting up 
        default values and callbacks.
        '''
        self.state_manager.init_state(
            'active_scanner', constants.DEFAULT_ACTIVE_SCANNER, 
            self._active_scanner_changed)
        self.state_manager.init_state(
            'scan_mode', constants.DEFAULT_SCAN_MODE, 
            self._scan_mode_changed)
        self.state_manager.init_state(
            'scan_resolution', constants.DEFAULT_SCAN_RESOLUTION, 
            self._scan_resolution_changed)
        self.state_manager.init_state(
            'thumbnail_size', constants.DEFAULT_THUMBNAIL_SIZE, 
            self._thumbnail_size_changed)
        self.state_manager.init_state(
            'show_toolbar', True, 
            self._show_toolbar_changed)
        self.state_manager.init_state(
            'show_thumbnails', True, 
            self._show_thumbnails_changed)
        self.state_manager.init_state(
            'show_statusbar', True, 
            self._show_statusbar_changed)
        self.state_manager.init_state(
            'save_path', os.path.expanduser('~'), 
            self._save_path_changed)        
        self.state_manager.init_state(
            'pdf_author', 'Author', 
            self._pdf_author_changed)
            
    # State-change callbacks
    
    def _active_scanner_changed(self):
        # TODO
        pass
    
    def _scan_mode_changed(self):
        '''
        Selects the chosen scan mode from the menu, or, if the selection
        is invalid, selects a safe alternative.
        
        Should always be called as a callback by the state_manager.
        Internal changes are handled in L{update_scan_mode}.
        '''
        menu_items = self.gui.scan_mode_sub_menu.get_children()
        
        # Nothing to select
        if not menu_items:
            return
        
        # Select the menu item that matches the new value
        for menu_item in menu_items:
            if menu_item.get_children()[0].get_text() == \
               self.state_manager['scan_mode']:
                menu_item.set_active(True)
                return
            
        # If not menu item matches set to first available and update
        # state_manager.
        logging.getLogger().debug('The value %s is not a valid scan mode.  \
            Scan mode will be reset to the first valid setting available.' %
            self.state_manager['scan_mode'])
        
        menu_items[0].set_active(True)
        self.state_manager['scan_mode'] = \
            menu_items[0].get_children()[0].get_text()
    
    def _scan_resolution_changed(self):
        '''
        Selects the chosen scan resolution from the menu, or, if the selection
        is invalid, selects a safe alternative.
        
        Should always be called as a callback by the state_manager.
        Internal changes are handled in L{update_scan_resolution}.
        '''
        menu_items = self.gui.scan_resolution_sub_menu.get_children()
        
        # Nothing to select
        if not menu_items:
            return
        
        # Select the menu item that matches the new value
        for menu_item in menu_items:
            if menu_item.get_children()[0].get_text() == \
               self.state_manager['scan_resolution']:
                menu_item.set_active(True)
                return
            
        # If not menu item matches set to first available and update
        # state_manager.
        logging.getLogger().debug('The value %s is not a valid scan resolution.  \
            Scan resolution will be reset to the first valid setting available.' %
            self.state_manager['scan_resolution'])
        
        menu_items[0].set_active(True)
        self.state_manager['scan_resolution'] = \
            menu_items[0].get_children()[0].get_text()
    
    def _thumbnail_size_changed(self):
        # TODO: update preferences dialogue and visible size
        pass
    
    def _show_toolbar_changed(self):
        '''
        Shows or hides the toolbar based on changes made to the 
        'show_toolbar' state.
        '''
        self.update_toolbar_visibility()
    
    def _show_thumbnails_changed(self):
        '''
        Shows or hides the thumbnails based on changes made to the 
        'show_thumbnails' state.
        '''
        self.update_thumbnails_visibility()
    
    def _show_statusbar_changed(self):
        '''
        Shows or hides the statusbar based on changes made to the 
        'show_statusbar' state.
        '''
        self.update_statusbar_visibility()
    
    def _save_path_changed(self):
        '''
        The save_path does not cause any updates as it is only
        visible in the save dialog, which is refreshed on
        each run.
        '''
        pass
    
    def _pdf_author_changed(self):
        '''
        The pdf_author does not cause any updates as it is only
        visible in the metadata_dialog, which is refreshed on
        each run.
        '''
        pass

    # Functions called by gui signal handlers
    
    def quit(self):
        '''
        Called when ScanWindow is destroyed to cleanup threads and files.
        '''
        self.quit_event.set()
        
        try:
            for scanned_page in self.scanned_pages:
                os.remove(scanned_page.path)
        finally:
            logging.getLogger().debug('Application quit.')
            gtk.main_quit()
        
    def scan_page(self):
        '''
        Starts the scanning thread.
        '''
        assert not self.scan_event.isSet(), 'Scanning in progress.'
        self.scan_thread(len(self.scanned_pages))
        
    def save_as(self):
        '''
        Gets PDF Metadata from the user, prompts for a filename, and 
        saves the document to PDF.
        '''
        assert not self.scan_event.isSet(), 'Scanning in progress.'
            
        if len(self.scanned_pages) < 1:
            self.gui.error_box(
                self.gui.scan_window, 'No pages have been scanned.')
            return
        
        # Save dialog
        filename_filter = gtk.FileFilter()
        filename_filter.set_name('PDF Files')
        filename_filter.add_mime_type('application/pdf')
        filename_filter.add_pattern('*.pdf')
        self.gui.save_dialog.add_filter(filename_filter)
        
        save_path = self.state_manager['save_path']
        if not os.path.exists(save_path):
            save_path = os.path.expanduser('~')
        self.gui.save_dialog.set_current_folder(save_path)
        self.gui.save_dialog.set_current_name('')
        
        response = self.gui.save_dialog.run()
        self.gui.save_dialog.hide()
        
        if response != gtk.RESPONSE_ACCEPT:
            return
        
        filename = self.gui.save_dialog.get_filename()
        filename_filter = self.gui.save_dialog.get_filter()
        
        if filename_filter.get_name() == 'PDF Files' and \
           filename[-4:] != '.pdf':
            filename = ''.join([filename, '.pdf'])
        
        # PDF metadata dialog
        title = filename.split('/')[-1][0:-4]
        author = self.state_manager['pdf_author']
        keywords = ''
        
        self.gui.title_entry.set_text(title)
        self.gui.author_entry.set_text(author)
        self.gui.keywords_entry.set_text(keywords)
        
        while 1:
            response = self.gui.metadata_dialog.run()
        
            if response != gtk.RESPONSE_APPLY:
                self.gui.metadata_dialog.hide()
                return
            
            title = unicode(self.gui.title_entry.get_text())
            author = unicode(self.gui.author_entry.get_text())
            keywords = unicode(self.gui.keywords_entry.get_text())
        
            if title == '':
                self.gui.error_box(
                    self.gui.scan_window, 
                    'You must provide a title for this document.')
            else:
                break
            
        self.gui.metadata_dialog.hide()
        self.gui.scan_window.window.set_cursor(
            gtk.gdk.Cursor(gtk.gdk.WATCH))
        gtk.gdk.flush()
        self.state_manager['pdf_author'] =  str(author)

        # Setup output pdf
        pdf = PdfCanvas(filename)
        pdf.setTitle(title)
        pdf.setAuthor(author)
        pdf.setKeywords(keywords)
            
        # Generate pages
        for i in range(len(self.scanned_pages)):    
            pil_image = self.scanned_pages[i].get_transformed_pil_image()
            
            # Write transformed image
            temp_file_path = os.path.join(
                constants.TEMP_IMAGES_DIRECTORY, 'temp%i.bmp' % i)
            pil_image.save(temp_file_path)
        
            assert os.path.exists(temp_file_path), \
                'Temporary bitmap file was not created by PIL.'
            
            image_width_in_inches = \
                pil_image.size[0] / int(self.state_manager['scan_resolution'])
            image_height_in_inches = \
                pil_image.size[1] / int(self.state_manager['scan_resolution'])
            
            # NB: Because not all SANE backends support specifying the size
            # of the scan area, the best we can do is scan at the default
            # setting and then convert that to an appropriate PDF.  For the
            # vast majority of scanners we hope that this would be either
            # letter or A4.
            pdf_width, pdf_height = self.find_best_fitting_pagesize(
                image_width_in_inches, image_height_in_inches)
                
            pdf.setPageSize((pdf_width, pdf_height))
            pdf.drawImage(
                temp_file_path, 
                0, 0, width=pdf_width, height=pdf_height, 
                preserveAspectRatio=True)
            pdf.showPage()
            
        # Save complete PDF
        pdf.save()
            
        assert os.path.exists(filename), \
            'Final PDF file was not created by ReportLab.'
        
        # Clean up
        # TODO - try block
        for i in range(len(self.scanned_pages)):
            os.remove(self.scanned_pages[i].path)
            os.remove(os.path.join(
                constants.TEMP_IMAGES_DIRECTORY, 'temp%i.bmp' % i))
        
        self.state_manager['save_path'] = \
            self.gui.save_dialog.get_current_folder()
        
        self.gui.preview_image_display.clear()
        self.gui.thumbnails_list_store.clear()
        
        self.gui.set_file_controls_sensitive(False)
        self.gui.set_delete_controls_sensitive(False)
        self.gui.set_zoom_controls_sensitive(False)
        self.gui.set_adjustment_controls_sensitive(False)        
        self.gui.set_navigation_controls_sensitive(False)    
        
        self.scanned_pages = []
        self.next_scan_file_index = 1
        self.preview_index = 0
        self.update_status()
        
        self.gui.scan_window.window.set_cursor(None)
        
    def find_best_fitting_pagesize(self, width_in_inches, height_in_inches):
        '''
        Searches through the possible page sizes and finds the one that
        best fits the image without cropping.
        '''        
        image_width_in_points = width_in_inches * points_per_inch
        image_height_in_points = height_in_inches * points_per_inch
        
        nearest_size = None
        nearest_distance = sys.maxint
        
        for size in constants.PAGESIZES.values():
            # Orient the size to match the page
            if image_width_in_points > image_height_in_points:
                size = landscape(size)
            else:
                size = portrait(size)
            
            # Only compare the size if its large enough to contain the entire 
            # image
            if size[0] < image_width_in_points or \
               size[1] < image_height_in_points:
                continue
            
            # Compute distance for comparison
            distance = \
                size[0] - image_width_in_points + \
                size[1] - image_height_in_points
            
            # Save if closer than prior nearest distance
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_size = size
                
                # Stop searching if a perfect match is found
                if nearest_distance == 0:
                    break
                
            assert nearest_size != None, 'No nearest size found.'
                
        return nearest_size
                    
    def delete_selected_page(self):
        '''
        Deletes the page currently selected in the thumbnail pager.
        '''
        if len(self.scanned_pages) < 1 or self.thumbnail_selection is None:
            return
    
        # TODO: catch exception when file does not exist
        os.remove(scanned_page.path)
        del self.scanned_pages[self.thumbnail_selection]
        
        delete_iter = self.gui.thumbnails_list_store.get_iter(
            self.thumbnail_selection)
        self.gui.thumbnails_list_store.remove(delete_iter)
        
        self.gui.preview_image_display.clear()
        self.gui.preview_horizontal_scroll.hide()
        self.gui.preview_vertical_scroll.hide()
        
        if len(self.scanned_pages) < 1:
            self.gui.set_file_controls_sensitive(False)        
            self.gui.set_delete_controls_sensitive(False)
            self.gui.set_zoom_controls_sensitive(False)
            self.gui.set_adjustment_controls_sensitive(False)    
        
        if len(self.scanned_pages) < 2:
            self.gui.set_navigation_controls_sensitive(False)
        
        if self.thumbnail_selection <= len(self.scanned_pages) - 1:
            self.gui.thumbnails_tree_view.get_selection().select_path(
                self.thumbnail_selection)
            self.gui.thumbnails_tree_view.scroll_to_cell(
                self.thumbnail_selection)
        elif len(self.scanned_pages) > 0:
            self.gui.thumbnails_tree_view.get_selection().select_path(
                self.thumbnail_selection - 1)
            self.gui.thumbnails_tree_view.scroll_to_cell(
                self.thumbnail_selection - 1)
        
    def insert_scan(self):
        '''
        Scans a page and inserts it before the current selected thumbnail.
        '''
        assert not self.scan_event.isSet(), 'Scanning in progress.'
        self.scan_thread(self.thumbnail_selection)
        
    def show_preferences(self):
        '''
        Show the preferences dialog.
        '''
        assert not self.scan_event.isSet(), 'Scanning in progress.'
        
        self.gui.preferences_dialog.run()
        self.gui.preferences_dialog.hide()
        
    def update_toolbar_visibility(self):
        '''
        Updates the visiblity of the toolbar based on the state
        in the state_manager.
        '''
        if self.state_manager['show_toolbar']:
            self.gui.show_toolbar_menu_item.set_active(True)
            self.gui.toolbar.show()
        else:
            self.gui.show_toolbar_menu_item.set_active(False)
            self.gui.toolbar.hide()
    
    def update_statusbar_visibility(self):
        '''
        Updates the visiblity of the statusbar based on the state
        in the state_manager.
        '''
        if self.state_manager['show_statusbar']:
            self.gui.show_statusbar_menu_item.set_active(True)
            self.gui.statusbar.show()
        else:
            self.gui.show_statusbar_menu_item.set_active(False)
            self.gui.statusbar.hide()
    
    def update_thumbnails_visibility(self):
        '''
        Updates the visiblity of the thumbnails based on the state
        in the state_manager.
        '''
        if self.state_manager['show_thumbnails']:
            self.gui.show_thumbnails_menu_item.set_active(True)
            self.gui.thumbnails_scrolled_window.show()
        else:
            self.gui.show_thumbnails_menu_item.set_active(False)
            self.gui.thumbnails_scrolled_window.hide()
        
    def zoom_in(self):
        '''
        Zooms the preview image in by 50%.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        if self.preview_zoom == 5:
            return
            
        self.preview_zoom +=  0.5
        
        if self.preview_zoom > 5:
            self.preview_zoom = 5
            
        self.preview_is_best_fit = False
            
        self.render_preview()
        self.update_status()
        
    def zoom_out(self):
        '''
        Zooms the preview image out by 50%.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        if self.preview_zoom == 0.5:
            return
            
        self.preview_zoom -=  0.5
        
        if self.preview_zoom < 0.5:
            self.preview_zoom = 0.5
            
        self.preview_is_best_fit = False
            
        self.render_preview()
        self.update_status()
        
    def zoom_one_to_one(self):
        '''
        Zooms the preview image to exactly 100%.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        self.preview_zoom =  1.0
            
        self.preview_is_best_fit = False
            
        self.render_preview()
        self.update_status()
        
    def zoom_best_fit(self):
        '''
        Zooms the preview image so that the entire image is displayed.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        width = self.preview_pixbuf.get_width()
        height = self.preview_pixbuf.get_height()
        
        width_ratio = float(width) / self.preview_width
        height_ratio = float(height) / self.preview_height
        
        if width_ratio < height_ratio:
            self.preview_zoom =  1 / float(height_ratio)
        else:
            self.preview_zoom =  1 / float(width_ratio)
            
        self.preview_is_best_fit = True
            
        self.render_preview()
        self.update_status()
        
    def rotate_counter_clockwise(self):
        '''
        Rotates the current page ninety degrees counter-clockwise, 
        or all pages if "rotate all pages" is toggled on.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        if self.gui.rotate_all_pages_menu_item.get_active():
            for scanned_page in self.scanned_pages:
                scanned_page.rotation += 90
        else:
            self.scanned_pages[self.preview_index].rotation += 90
            
        self.preview_pixbuf = \
            self.scanned_pages[self.preview_index].get_transformed_pixbuf()
        
        if self.preview_is_best_fit:
            self.zoom_best_fit()
        else:
            self.render_preview()
            self.update_status()
        
        if self.gui.rotate_all_pages_menu_item.get_active():
            for i in range(len(self.scanned_pages)):            
                self.update_thumbnail(i)
        else:
            self.update_thumbnail(self.preview_index)
        
    def rotate_clockwise(self):
        '''
        Rotates the current page ninety degrees clockwise, 
        or all pages if "rotate all pages" is toggled on.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        if self.gui.rotate_all_pages_menu_item.get_active():
            for scanned_page in self.scanned_pages:
                scanned_page.rotation -= 90
        else:
            self.scanned_pages[self.preview_index].rotation -= 90
            
        self.preview_pixbuf = \
            self.scanned_pages[self.preview_index].get_transformed_pixbuf()
        
        if self.preview_is_best_fit:
            self.zoom_best_fit()
        else:
            self.render_preview()
            self.update_status()
        
        if self.gui.rotate_all_pages_menu_item.get_active():
            for i in range(len(self.scanned_pages)):            
                self.update_thumbnail(i)
        else:
            self.update_thumbnail(self.preview_index)
                    
    def adjust_colors_toggle(self):
        '''
        Toggles the visibility of the adjust colors dialog.
        '''
        if self.gui.adjust_colors_menu_item.get_active():
            self.gui.adjust_colors_window.show()
        else:
            self.gui.adjust_colors_window.hide()
    
    def update_scan_mode(self, widget):
        '''
        Updates the internal scan mode state when a scan mode menu 
        item is toggled.
        '''
        try:
            if widget.get_active():
                self.state_manager['scan_mode'] = \
                    widget.get_children()[0].get_text()
        except:
            # TODO: this should really bubble up and be treated as a breaking
            # error.
            logging.getLogger().error(
                'Unable to get label text for currently selected scan mode \
                menu item.', exc_info=True)
            raise
        
    def update_scan_resolution(self, widget):
        '''
        Updates the internal scan resolution state when a scan resolution 
        menu item is toggled.
        '''
        try:
            if widget.get_active():
                self.state_manager['scan_resolution'] = \
                    widget.get_children()[0].get_text()
        except:
            # TODO: this should really bubble up and be treated as a breaking
            # error.
            logging.getLogger().error(
                'Unable to get label text for currently selected scan resolution \
                menu item.', exc_info=True)
            raise
        
    def goto_first_page(self):
        '''Moves to the first scanned page.'''
        if len(self.scanned_pages) < 1:
            return
            
        self.gui.thumbnails_tree_view.get_selection().select_path(0)
        self.gui.thumbnails_tree_view.scroll_to_cell(0)
        
    def goto_previous_page(self):
        '''
        Moves to the previous scanned page.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        if self.preview_index < 1:
            return
            
        self.gui.thumbnails_tree_view.get_selection().select_path(
            self.preview_index - 1)
        self.gui.thumbnails_tree_view.scroll_to_cell(self.preview_index - 1)
        
    def goto_next_page(self):
        '''
        Moves to the next scanned page.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        if self.preview_index >= len(self.scanned_pages) - 1:
            return
            
        self.gui.thumbnails_tree_view.get_selection().select_path(
            self.preview_index + 1)
        self.gui.thumbnails_tree_view.scroll_to_cell(self.preview_index + 1)
        
    def goto_last_page(self):
        '''
        Moves to the last scanned page.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        self.gui.thumbnails_tree_view.get_selection().select_path(
            len(self.scanned_pages) - 1)
        self.gui.thumbnails_tree_view.scroll_to_cell(
            len(self.scanned_pages) - 1)
        
    def show_about(self):
        '''
        Show the about dialog.
        '''            
        self.gui.about_dialog.run()
        self.gui.about_dialog.hide()
        
    def update_brightness(self):
        '''
        Updates the brightness of the current page, or all pages if the 
        color_all_pages_check is toggled on.
        '''
        if len(self.scanned_pages) < 1:
            return
            
        self.gui.adjust_colors_window.window.set_cursor(
            gtk.gdk.Cursor(gtk.gdk.WATCH))
            
        self.scanned_pages[self.preview_index].brightness = \
            self.gui.brightness_scale.get_value()
        self.preview_pixbuf = \
             self.scanned_pages[self.preview_index].get_transformed_pixbuf()
        self.render_preview()
        self.update_thumbnail(self.preview_index)
        
        if self.gui.color_all_pages_check.get_active() and \
           len(self.scanned_pages) > 1:
            for index in range(len(self.scanned_pages)):
                if index != self.preview_index:
                    self.scanned_pages[index].brightness = \
                        self.gui.brightness_scale.get_value()
                    self.update_thumbnail(index)
                    
        self.gui.adjust_colors_window.window.set_cursor(None)
        
    def update_contrast(self):        
        '''
        Updates the contrast of the current page, or all pages if the 
        color_all_pages_check is toggled on.
        '''    
        if len(self.scanned_pages) < 1:
            return
            
        self.scanned_pages[self.preview_index].contrast = \
            self.gui.contrast_scale.get_value()
        self.preview_pixbuf = \
            self.scanned_pages[self.preview_index].get_transformed_pixbuf()
        self.render_preview()
        self.update_thumbnail(self.preview_index)
        
        if self.gui.color_all_pages_check.get_active() and \
           len(self.scanned_pages) > 1:
            for index in range(len(self.scanned_pages)):
                if index != self.preview_index:
                    self.scanned_pages[index].contrast = \
                        self.gui.contrast_scale.get_value()
                    self.update_thumbnail(index)
        
    def update_sharpness(self):    
        '''
        Updates the sharpness of the current page, or all pages if the 
        color_all_pages_check is toggled on.
        '''        
        if len(self.scanned_pages) < 1:
            return
        
        self.scanned_pages[self.preview_index].sharpness = \
            self.gui.sharpness_scale.get_value()
        self.preview_pixbuf = \
            self.scanned_pages[self.preview_index].get_transformed_pixbuf()
        self.render_preview()
        self.update_thumbnail(self.preview_index)
        
        if self.gui.color_all_pages_check.get_active() and \
           len(self.scanned_pages) > 1:
            for index in range(len(self.scanned_pages)):
                if index != self.preview_index:
                    self.scanned_pages[index].sharpness = \
                        self.gui.sharpness_scale.get_value()
                    self.update_thumbnail(index)
            
    def color_all_pages_toggled(self):
        '''
        Catches the color_all_pages_check being toggled on so that all 
        per-page settings can be immediately synchronized.
        '''
        if self.gui.color_all_pages_check.get_active():
            for index in range(len(self.scanned_pages)):
                if index != self.preview_index:
                    self.scanned_pages[index].brightness = \
                        self.gui.brightness_scale.get_value()
                    self.scanned_pages[index].contrast = \
                        self.gui.contrast_scale.get_value()
                    self.scanned_pages[index].sharpness = \
                        self.gui.sharpness_scale.get_value()
                    self.update_thumbnail(index)

    def preview_resized(self, rect):
        '''
        Catches preview display size allocations so that the preview image
        can be appropriately scaled to fit the display.
        '''
        if rect.width == self.preview_width and \
           rect.height == self.preview_height:
            return
            
        self.preview_width = rect.width
        self.preview_height = rect.height
        
        if len(self.scanned_pages) < 1:
            return
            
        #~ if self.scan_event.isSet():
            #~ return
        
        if self.preview_is_best_fit:
            self.zoom_best_fit()
        else:
            self.render_preview()
            self.update_status()
        
    def preview_button_pressed(self, event):
        '''
        Catches button presses on the preview display and traps the coords 
        for dragging.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        if event.button == 1:
            if self.gui.preview_horizontal_scroll.get_property('visible') or \
               self.gui.preview_vertical_scroll.get_property('visible') :
                self.gui.preview_image_display.get_parent_window().set_cursor(
                    gtk.gdk.Cursor(gtk.gdk.FLEUR))
        elif event.button == 3:
            self.zoom_drag_start_x, self.zoom_drag_start_y = event.x, event.y
            self.gui.preview_image_display.get_parent_window().set_cursor(
                gtk.gdk.Cursor(gtk.gdk.CROSS))
            
    def preview_button_released(self, event):
        '''
        Handles actual zoom part of the drag-to-zoom bejavior.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        if event.button == 1:
            self.gui.preview_image_display.get_parent_window().set_cursor(
                None)
        elif event.button == 3:      
            # Transform to absolute coords
            start_x = self.zoom_drag_start_x / self.preview_zoom
            start_y = self.zoom_drag_start_y / self.preview_zoom
            end_x = event.x / self.preview_zoom
            end_y = event.y / self.preview_zoom
            
            # Swizzle values if coords are reversed
            if end_x < start_x:
                start_x, end_x = end_x, start_x
                
            if end_y < start_y:
                start_y, end_y = end_y, start_y
            
            # Calc width and height
            width = end_x - start_x
            height = end_y - start_y
            
            # Calculate centering offset
            target_width =  \
                self.preview_pixbuf.get_width() * self.preview_zoom
            target_height = \
                self.preview_pixbuf.get_height() * self.preview_zoom
            
            shift_x = int((self.preview_width - target_width) / 2)
            if shift_x < 0:
                shift_x = 0
            shift_y = int((self.preview_height - target_height) / 2)
            if shift_y < 0:
                shift_y = 0
            
            # Compensate for centering
            start_x -= shift_x / self.preview_zoom
            start_y -= shift_y / self.preview_zoom
            
            # Determine center-point of zoom region
            center_x = start_x + width / 2
            center_y = start_y + height / 2
            
            # Determine correct zoom to fit region
            if width > height:
                self.preview_zoom = self.preview_width / width
            else:
                self.preview_zoom = self.preview_height / height
                
            # Cap zoom at 500%
            if self.preview_zoom > 5.0:
                self.preview_zoom = 5.0
                
            # Transform center-point to relative coords            
            transform_x = int(center_x * self.preview_zoom)
            transform_y = int(center_y * self.preview_zoom)
            
            # Center in preview display
            transform_x -= int(self.preview_width / 2)
            transform_y -= int(self.preview_height / 2)
            
            self.preview_is_best_fit = False
            self.render_preview()
            
            self.gui.preview_layout.get_hadjustment().set_value(transform_x)
            self.gui.preview_layout.get_vadjustment().set_value(transform_y)
            
            self.update_status()
            
            self.gui.preview_image_display.get_parent_window().set_cursor(
                None)   
        
    def preview_mouse_moved(self, event):
        '''
        Handles motion element of the drag-to-move/drag-to-zoom behavior 
        for the preview display.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        if event.is_hint:
            mouse_x, mouse_y, mouse_state = event.window.get_pointer()
        else:
            mouse_state = event.state
            
        mouse_x, mouse_y = event.x_root, event.y_root
        
        # Move
        if (mouse_state & gtk.gdk.BUTTON1_MASK):
            horizontal_adjustment = self.gui.preview_layout.get_hadjustment()
            
            new_x = horizontal_adjustment.value + \
                (self.preview_drag_start[0] - mouse_x)
                            
            if new_x >= horizontal_adjustment.lower and \
               new_x <= horizontal_adjustment.upper - horizontal_adjustment.page_size:
                horizontal_adjustment.set_value(new_x)
                
            vertical_adjustment = self.gui.preview_layout.get_vadjustment()
            new_y = \
                vertical_adjustment.value + \
                    (self.preview_drag_start[1] - mouse_y)
            
            if new_y >= vertical_adjustment.lower and \
               new_y <= vertical_adjustment.upper - vertical_adjustment.page_size:
                vertical_adjustment.set_value(new_y)
        # Zoom
        elif (mouse_state & gtk.gdk.BUTTON3_MASK):
            start_x = self.zoom_drag_start_x
            start_y = self.zoom_drag_start_y
            end_x = event.x
            end_y = event.y
            
            if end_x < start_x:
                start_x, end_x = end_x, start_x
                
            if end_y < start_y:
                start_y, end_y = end_y, start_y
            
            width = end_x - start_x
            height = end_y - start_y

            self.gui.preview_image_display.set_from_pixbuf(self.scaled_pixbuf)
            self.gui.preview_image_display.get_parent_window().invalidate_rect(
                (0, 0, self.preview_width, self.preview_height), 
                False)
            self.gui.preview_image_display.get_parent_window(). \
                process_updates(False)
            
            graphics_context = \
                self.gui.preview_image_display.get_parent_window().new_gc(
                    foreground=self.preview_zoom_rect_color, 
                    line_style=gtk.gdk.LINE_ON_OFF_DASH, 
                    line_width=2)
                
            self.gui.preview_image_display.get_parent_window().draw_rectangle(
                graphics_context, 
                False, 
                int(start_x), int(start_y), 
                int(width), int(height))
            
        self.preview_drag_start = (mouse_x, mouse_y)
        
    def preview_scrolled(self, event):
        '''
        Use scroll events to loop through scanned pages.
        '''
        if len(self.scanned_pages) < 1:
            return
        
        # TODO: remove?
#        current_x = self.gui.preview_layout.get_hadjustment()
#        current_y = self.gui.preview_layout.get_vadjustment()
#        new_x = current_x.value
#        new_y = current_y.value
        
        if event.direction == gtk.gdk.SCROLL_UP:
            self.goto_previous_page()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.goto_next_page()        
            
    def thumbnail_inserted(self, treemodel, path, tree_iter):
        '''
        Catches when a thumbnail is inserted in the list and, if it is the result 
        of a drag-and-drop operation, reorders the list of scanned pages to 
        match.
        '''
        if self.insert_is_not_drag:
            self.insert_is_not_drag = False
            return
            
        dest_path = path[0]
        
        temp = self.scanned_pages[self.thumbnail_selection]
        del  self.scanned_pages[self.thumbnail_selection]
        
        if dest_path > self.thumbnail_selection:
            self.scanned_pages.insert(dest_path - 1, temp)
        else:
            self.scanned_pages.insert(dest_path, temp)
        
    def thumbnail_selected(self, selection):
        '''
        Catches when a thumbnail is selected, stores its index, and displays 
        the proper image.
        '''
        selection_iter = selection.get_selected()[1]
        
        if not selection_iter:
            return
        
        scan_index = self.gui.thumbnails_list_store.get_path(selection_iter)[0]
        self.thumbnail_selection = scan_index
        self.jump_to_page(scan_index)
        
    # Functions not called from gui signal handlers
            
    def add_page(self, index, new_page):
        '''
        Appends or inserts a page into the list of scanned pages.
        
        @param index: The index in the list at which to insert the new page.
        @type index: int
        
        @param new_page: The L{Page} object to add to the list.
        @type new_page: Page
        '''
        self.insert_is_not_drag = True
        
        if not index:
            index = 0
        
        if index > len(self.scanned_pages) - 1:
            self.scanned_pages.append(new_page)
            self.gui.thumbnails_list_store.append(
                [new_page.get_thumbnail_pixbuf(self.thumbnail_size)])
            self.gui.thumbnails_tree_view.get_selection().select_path(
                len(self.scanned_pages) - 1)
            self.gui.thumbnails_tree_view.scroll_to_cell(
                len(self.scanned_pages) - 1)
        else:
            self.scanned_pages.insert(index, new_page)
            self.gui.thumbnails_list_store.insert(
                index, [new_page.get_thumbnail_pixbuf(self.thumbnail_size)])
            self.gui.thumbnails_tree_view.get_selection().select_path(index)
            self.gui.thumbnails_tree_view.scroll_to_cell(index)
        
    def jump_to_page(self, index):
        '''
        Moves to a specified scanned page.
        '''
        assert index >= 0 and index < len(self.scanned_pages), \
            'Page index out of bounds.'
            
        self.preview_index = index
        
        self.gui.brightness_scale.set_value(
            self.scanned_pages[self.preview_index].brightness)
        self.gui.contrast_scale.set_value(
            self.scanned_pages[self.preview_index].contrast)
        self.gui.sharpness_scale.set_value(
            self.scanned_pages[self.preview_index].sharpness)
        
        self.preview_pixbuf = \
            self.scanned_pages[self.preview_index].get_transformed_pixbuf()
        
        if self.preview_is_best_fit:
            self.zoom_best_fit()
        else:
            self.render_preview()
            self.update_status()
    
    def update_status(self):
        '''
        Updates the status bar with the current page number and zoom 
        percentage.
        '''
        self.gui.statusbar.pop(constants.STATUSBAR_PREVIEW_CONTEXT_ID)
        
        if len(self.scanned_pages) > 0:
            self.gui.statusbar.push(
                constants.STATUSBAR_PREVIEW_CONTEXT_ID, 
                'Page %i of %i\t%i%%' % \
                    (self.preview_index + 1, 
                        len(self.scanned_pages), 
                        int(self.preview_zoom * 100)))
        
    def update_thumbnail(self, index):
        '''Updates a thumbnail image to match changes in the preview image.'''
        list_iter = self.gui.thumbnails_list_store.get_iter(index)
        thumbnail = self.scanned_pages[index].get_thumbnail_pixbuf(
            self.thumbnail_size)
        self.gui.thumbnails_list_store.set_value(list_iter, 0, thumbnail)
        
    def render_preview(self):
        '''
        Render the current page to the preview display.
        '''
        assert len(self.scanned_pages) > 0, \
            'Render request made when no pages have been scanned.'
        
        # Zoom if necessary
        if self.preview_zoom != 1.0:
            target_width = \
                int(self.preview_pixbuf.get_width() * self.preview_zoom)
            target_height = \
                int(self.preview_pixbuf.get_height() * self.preview_zoom)
            
            self.scaled_pixbuf = self.preview_pixbuf.scale_simple(
                target_width, target_height, gtk.gdk.INTERP_BILINEAR)
        else:
            target_width = self.preview_pixbuf.get_width()
            target_height = self.preview_pixbuf.get_height()
            
            self.scaled_pixbuf = self.preview_pixbuf
        
        # Resize preview area
        self.gui.preview_layout.set_size(target_width, target_height)
        
        # Center preview
        shift_x = int((self.preview_width - target_width) / 2)
        if shift_x < 0:
            shift_x = 0
        shift_y = int((self.preview_height - target_height) / 2)
        if shift_y < 0:
            shift_y = 0
        self.gui.preview_layout.move(
            self.gui.preview_image_display, shift_x, shift_y)
        
        # Show/hide scrollbars
        if target_width > self.preview_width:
            self.gui.preview_horizontal_scroll.show()
        else:
            self.gui.preview_horizontal_scroll.hide()
            
        if target_height > self.preview_height:
            self.gui.preview_vertical_scroll.show()
        else:
            self.gui.preview_vertical_scroll.hide()
        
        # Render updated preview
        self.gui.preview_image_display.set_from_pixbuf(self.scaled_pixbuf)
                    
    def update_scanner_list(self, widget=None):
        '''
        Populates a menu with a list of available scanners.
        '''
        #assert not self.scan_event.isSet(), 'Scanning in progress.'
        
        # Clear existing menu items
        for child in self.gui.scanner_sub_menu.get_children():
            self.gui.scanner_sub_menu.remove(child)

        self.scanner_dict = scanning.get_available_scanners()
        
        scanners = self.scanner_dict.keys()
        first_item = None
        selected_item = None
        for i in range(len(scanners)):
            # The first menu item defines the group
            if i == 0:
                menu_item = gtk.RadioMenuItem(None, scanners[i])
                first_item = menu_item
            else:
                menu_item = gtk.RadioMenuItem(first_item, scanners[i])
                
            if i == 0 and self.active_scanner not in scanners:
                menu_item.set_active(True)
                selected_item = menu_item
            
            if scanners[i] == self.active_scanner:
                menu_item.set_active(True)
                selected_item = menu_item
            
            menu_item.connect('toggled', self.update_scanner_options)
            self.gui.scanner_sub_menu.append(menu_item)
        
        menu_item = gtk.MenuItem('Refresh List')
        menu_item.connect('activate', self.update_scanner_list)
        self.gui.scanner_sub_menu.append(menu_item)
        
        self.gui.scanner_sub_menu.show_all()
        
        # Emulate the default scanner being toggled
        self.update_scanner_options(selected_item)
        
        # Notify user if no scanners are connected
        if selected_item == None:
            self.gui.statusbar.push(
                constants.STATUSBAR_SCANNER_STATUS_CONTEXT_ID, 
                'No scanners available')
        else:
            self.gui.statusbar.pop(
            constants.STATUSBAR_SCANNER_STATUS_CONTEXT_ID)

    def update_scanner_options(self, widget=None):
        '''
        Populates a menu with a list of available options for the currently 
        selected scanner.
        
        @param widget: The selected menu item.  None if no scanners are
            available.
        @type widget: gtk.MenuItem.
        '''
        #assert not self.scan_event.isSet(), 'Scanning in progress.'
        
        # Clear scan modes sub menu
        for child in self.gui.scan_mode_sub_menu.get_children():
            self.gui.scan_mode_sub_menu.remove(child)
        
        # Clear scan resolutions sub menu
        for child in self.gui.scan_resolution_sub_menu.get_children():
            self.gui.scan_resolution_sub_menu.remove(child)
        
        # No available scanners
        if (widget == None):            
            menu_item = gtk.MenuItem('No Scanner Selected')
            self.gui.scan_mode_sub_menu.append(menu_item)
            self.gui.scan_mode_sub_menu.show_all()
            
            menu_item = gtk.MenuItem('No Scanner Selected')
            self.gui.scan_resolution_sub_menu.append(menu_item)
            self.gui.scan_resolution_sub_menu.show_all()
            
            self.active_scanner = None
            self.gui.set_scan_controls_sensitive(False)
            
            return
        
        # Get the selected scanner
        toggled_scanner = widget.get_children()[0].get_text()
        
        # Get new scanner options
        self.active_scanner = toggled_scanner   
        self.gui.set_scan_controls_sensitive(True)
                
        mode_list, resolution_list = scanning.get_scanner_options(
            self.scanner_dict[self.active_scanner])
        
        # Generate new scan mode menu
        if not mode_list:
            menu_item = gtk.MenuItem("No Scan Modes")
            menu_item.set_sensitive(False)
            self.gui.scan_mode_sub_menu.append(menu_item)
        else:        
            for i in range(len(mode_list)):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(None, mode_list[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(first_item, mode_list[i])
                    
                if i == 0 and self.state_manager['scan_mode'] not in mode_list:
                    menu_item.set_active(True)
                    selected_item = menu_item
                
                if mode_list[i] == self.state_manager['scan_mode']:
                    menu_item.set_active(True)
                    selected_item = menu_item
                
                menu_item.connect('toggled', self.update_scan_mode)
                self.gui.scan_mode_sub_menu.append(menu_item)
            
        self.gui.scan_mode_sub_menu.show_all()
        
        # Emulate the default scan mode being toggled
        self.update_scan_mode(selected_item)
        
        # Generate new resolution menu
        if not resolution_list:
            menu_item = gtk.MenuItem("No Resolutions")
            self.gui.scan_resolution_sub_menu.append(menu_item)
            menu_item.set_sensitive(False)
        else:        
            for i in range(len(resolution_list)):
                if i == 0:
                    menu_item = gtk.RadioMenuItem(None, resolution_list[i])
                    first_item = menu_item
                else:
                    menu_item = gtk.RadioMenuItem(first_item, resolution_list[i])
                    
                if i == 0 and \
                   self.state_manager['scan_resolution'] not in resolution_list:
                    menu_item.set_active(True)
                    selected_item = menu_item
                
                if resolution_list[i] == self.state_manager['scan_resolution']:
                    menu_item.set_active(True)
                    selected_item = menu_item
                
                menu_item.connect('toggled', self.update_scan_resolution)
                self.gui.scan_resolution_sub_menu.append(menu_item)
            
        self.gui.scan_resolution_sub_menu.show_all()
        
        # Emulate the default scan resolution being toggled
        self.update_scan_resolution(selected_item)
        
        # NB: Only do this if everything else has succeeded, 
        # otherwise a crash could repeat everytime the app is started
        self.state_manager['active_scanner'] = self.active_scanner
    
    @threaded
    def scan_thread(self, index):
        '''
        Scans a page with "scanimage" and appends it to the end of the 
        current document.
        '''
        self.scan_event.set()
        
        gtk.gdk.threads_enter()
        
        self.gui.scan_window.window.set_cursor(
            gtk.gdk.Cursor(gtk.gdk.WATCH))        
        self.gui.set_file_controls_sensitive(False)
        self.gui.set_scan_controls_sensitive(False)
        self.gui.statusbar.push(
            constants.STATUSBAR_SCAN_CONTEXT_ID, 'Scanning...')
            
        gtk.gdk.threads_leave()
        
        # TODO: test for empty string as state_manager will never return
        # None
        assert self.state_manager['scan_mode'] != \
            None, 'Attempting to scan with no scan mode selected.'
        assert self.state_manager['scan_resolution'] != \
            None, 'Attempting to scan with no scan resolution selected.'
        assert self.active_scanner != \
            None, 'Attempting to scan with no scanner selected.'
        
        scan_path = os.path.join(
             constants.TEMP_IMAGES_DIRECTORY, 
             'scan%i.pnm' % self.next_scan_file_index)
        result = scanning.scan_to_file(
            self.scanner_dict[self.active_scanner], 
            self.state_manager['scan_mode'], 
            self.state_manager['scan_resolution'], 
            scan_path)
        
        if result == constants.SCAN_FAILURE:
            gtk.gdk.threads_enter()
            
            self.gui.statusbar.pop(constants.STATUSBAR_SCAN_CONTEXT_ID)
            self.gui.scan_window.window.set_cursor(None)
            self.gui.set_scan_controls_sensitive(True)
            if len(self.scanned_pages) > 0:
                self.gui.set_file_controls_sensitive(True)
                
            # Check that scan didn't fail because the scanner got unplugged
            self.update_scanner_list()
            if self.active_scanner == None:
                # TODO: Notify that scanner was disconnected
                pass
            else:
                # TODO: Notify that scan failed for reasons that aren't clear
                pass
                        
            gtk.gdk.threads_leave()
            
            self.scan_event.clear()
            return
            
        if self.quit_event.isSet():
            return
            
        if self.cancel_scan_event.isSet():
            gtk.gdk.threads_enter()
            self.gui.statusbar.pop(constants.STATUSBAR_SCAN_CONTEXT_ID)
            self.gui.scan_window.window.set_cursor(None)
            self.gui.set_scan_controls_sensitive(True)
            if (len(self.scanned_pages) > 0):
                self.gui.set_file_controls_sensitive(True)  
            gtk.gdk.threads_leave()
            self.scan_event.clear()
            return
        
        self.next_scan_file_index += 1
        
        scan_page = page.Page(
            scan_path, float(self.state_manager['scan_resolution']))
        
        gtk.gdk.threads_enter()
        
        if not self.gui.color_all_pages_check.get_active():
            self.gui.brightness_scale.set_value(1.0)
            self.gui.contrast_scale.set_value(1.0)
            self.gui.sharpness_scale.set_value(1.0)
            
        scan_page.brightness = self.gui.brightness_scale.get_value()
        scan_page.contrast = self.gui.contrast_scale.get_value()
        scan_page.sharpness = self.gui.sharpness_scale.get_value()
        
        self.add_page(index, scan_page)
        
        self.gui.statusbar.pop(constants.STATUSBAR_SCAN_CONTEXT_ID)
        self.gui.set_file_controls_sensitive(True)
        self.gui.set_scan_controls_sensitive(True)
        
        self.gui.set_delete_controls_sensitive(True)
        self.gui.set_zoom_controls_sensitive(True)
        self.gui.set_adjustment_controls_sensitive(True)    
        
        if len(self.scanned_pages) > 1:
            self.gui.set_navigation_controls_sensitive(True)
        
        self.gui.scan_window.window.set_cursor(None)        

        gtk.gdk.threads_leave()
        
        self.scan_event.clear()
