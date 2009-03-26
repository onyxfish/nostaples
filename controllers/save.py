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

"""
This module holds the L{SaveController}, which manages interaction 
between the L{SaveModel} and L{SaveView}.
"""

import logging
import os
import sys
import tempfile

import gtk
from gtkmvc.controller import Controller
import Image, ImageEnhance
from reportlab.pdfgen.canvas import Canvas as PdfCanvas
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.units import inch as points_per_inch
from reportlab.lib.units import mm as points_per_mm

from nostaples import constants
import nostaples.utils.gui

class SaveController(Controller):
    """
    Manages interaction between the L{SaveModel} and
    L{SaveView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, application):
        """
        Constructs the SaveController.
        """
        self.application = application
        Controller.__init__(self, application.get_save_model())
        
        status_controller = application.get_status_controller()
        self.status_context = \
            status_controller.get_context_id(self.__class__.__name__)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        preferences_model = self.application.get_preferences_model()
        save_model = self.application.get_save_model()
        
        # Force refresh of keyword list
        keywords_liststore = view['keywords_entry'].get_liststore()
        keywords_liststore.clear()
        
        for keyword in preferences_model.saved_keywords:
            keywords_liststore.append([keyword])
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    def register_adapters(self):
        """
        Registers adapters for property/widget pairs that do not require 
        complex processing.
        """
        self.adapt('title', 'title_entry')
        self.adapt('author', 'author_entry')
        self.adapt('keywords', 'keywords_entry')
        self.adapt('show_document_metadata', 'document_metadata_expander')
        self.log.debug('Adapters registered.')
        
    # USER INTERFACE CALLBACKS
    
    def on_title_from_filename_button_clicked(self, button):
        """
        Copy the selected filename to the pdf title property.
        """
        save_view = self.application.get_save_view()
        
        title = save_view['save_dialog'].get_filename()
        
        if not title:
            save_view['title_entry'].set_text('')
            return
        
        title = title.split('/')[-1]
        
        if title[-4:] == '.pdf':
            title = title[:-4]
        
        save_view['title_entry'].set_text(title)
        
    def on_clear_title_button_clicked(self, button):
        """Clear the title."""
        self.application.get_save_model().title = ''
    
    def on_clear_author_button_clicked(self, button):
        """Clear the author."""
        self.application.get_save_model().author = ''
    
    def on_clear_keywords_button_clicked(self, button):
        """Clear the keywords."""
        self.application.get_save_model().keywords = ''
        
    def on_save_dialog_response(self, dialog, response):
        """
        Determine the selected file type and invoke the method
        that saves that file type.
        """
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        main_view = self.application.get_main_view()
        
        save_view['save_dialog'].hide()
        
        if response != gtk.RESPONSE_ACCEPT:
            return
        
        main_view['scan_window'].window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        nostaples.utils.gui.flush_pending_events()
        
        save_model.filename = save_view['save_dialog'].get_filename()
        filename_filter = save_view['save_dialog'].get_filter()
        
        if filename_filter.get_name() == 'PDF Files':
            if save_model.filename[-4:] != '.pdf':
                save_model.filename = ''.join([save_model.filename, '.pdf'])
            self._save_pdf()
        else:
            self.log.error('Unknown file type: %s.' % save_model.filename)
            
        self._update_saved_keywords()
            
        main_view['scan_window'].window.set_cursor(None)
            
        save_model.save_path = save_view['save_dialog'].get_current_folder()
    
    # PROPERTY CALLBACKS
    
    def property_saved_keywords_value_change(self, model, old_value, new_value):
        """
        Update the keywords auto-completion control with the new
        keywords.
        """
        save_view = self.application.get_save_view()
        
        keywords_liststore = save_view['keywords_entry'].get_liststore()
        keywords_liststore.clear()
        
        for keyword in new_value:
            keywords_liststore.append([keyword])
        
    # PRIVATE METHODS
        
    def _save_pdf(self):
        """
        Output the current document to a PDF file using ReportLab.
        """
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        document_model = self.application.get_document_model()
        
        # TODO: seperate saving code into its own thread?
        
        # Setup output pdf
        pdf = PdfCanvas(save_model.filename)
        pdf.setTitle(save_model.title)
        pdf.setAuthor(save_model.author)
        pdf.setKeywords(save_model.keywords)
            
        # Generate pages
        page_iter = document_model.get_iter_first()
        while page_iter:
            current_page = document_model.get_value(page_iter, 0)
            
            # Write transformed image
            temp_file_path = ''.join([tempfile.mktemp(), '.bmp'])
            current_page.pil_image.save(temp_file_path)
        
            assert os.path.exists(temp_file_path), \
                'Temporary bitmap file was not created by PIL.'
            
            width_in_inches = \
                int(current_page.width / current_page.resolution)
            height_in_inches = \
                int(current_page.height / current_page.resolution)
            
            # NB: Because not all SANE backends support specifying the size
            # of the scan area, the best we can do is scan at the default
            # setting and then convert that to an appropriate PDF.  For the
            # vast majority of scanners we hope that this would be either
            # letter or A4.
            pdf_width, pdf_height = self._determine_best_fitting_pagesize(
                width_in_inches, height_in_inches)
                
            pdf.setPageSize((pdf_width, pdf_height))
            pdf.drawImage(
                temp_file_path, 
                0, 0, width=pdf_width, height=pdf_height, 
                preserveAspectRatio=True)
            pdf.showPage()
            
            os.remove(temp_file_path)
            
            page_iter = document_model.iter_next(page_iter)
            
        # Save complete PDF
        pdf.save()
            
        assert os.path.exists(save_model.filename), \
            'Final PDF file was not created by ReportLab.'
            
        document_model.clear()
    
    def _determine_best_fitting_pagesize(self, width_in_inches, height_in_inches):
        """
        Searches through the possible page sizes and finds the smallest one that
        will contain the image without cropping.
        """        
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
        
    def _update_saved_keywords(self):
        """
        Update the saved keywords with any new keywords that
        have been used.
        """
        preferences_model = self.application.get_preferences_model()
        save_model = self.application.get_save_model()
                        
        new_keywords = []        
        for keyword in save_model.keywords.split():
            if keyword not in preferences_model.saved_keywords:
                new_keywords.append(keyword)
                
        if new_keywords:
            temp_list = []
            temp_list.extend(preferences_model.saved_keywords)
            temp_list.extend(new_keywords)
            temp_list.sort()
            preferences_model.saved_keywords = temp_list
        
    # PUBLIC METHODS
    
    def run(self):
        """Run the save dialog."""
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        status_controller = self.application.get_status_controller()
        
        save_view['save_dialog'].set_current_folder(save_model.save_path)
        save_view['save_dialog'].set_current_name('')
        
        status_controller.push(self.status_context, 'Saving...')
        
        save_view.run()
        
        status_controller.pop(self.status_context)