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

import constants

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

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
        
    def on_save_dialog_response(self, dialog, response):
        """
        Determine the selected file type and invoke the method
        that saves that file type.
        """
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        
        save_view['save_dialog'].hide()
        
        if response != gtk.RESPONSE_ACCEPT:
            return
        
        save_model.filename = save_view['save_dialog'].get_filename()
        filename_filter = save_view['save_dialog'].get_filter()
        
        if save_model.filename[-4:] == '.pdf':
            self._save_pdf()
        elif filename_filter.get_name() == 'PDF Files':
            save_model.filename = ''.join([save_model.filename, '.pdf'])
            self._save_pdf()
        else:
            self.log.error('Unknown file type: %s.' % save_model.filename)
            
        save_model.save_path = save_view['save_dialog'].get_current_folder()
        
    def on_pdf_dialog_response(self, dialog, response):
        """
        Output the current document to a PDF file using ReportLab.
        """
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        document_model = self.application.get_document_model()
        
        save_view['pdf_dialog'].window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        gtk.gdk.flush()
            
        if response != gtk.RESPONSE_APPLY:
            return
        
        title = unicode(save_view['title_entry'].get_text())
        author = unicode(save_view['author_entry'].get_text())
        keywords = unicode(save_view['keywords_entry'].get_text())
        
        save_model.author = str(author)
        
        # TODO: seperate saving code into its own thread
        
        # Setup output pdf
        pdf = PdfCanvas(save_model.filename)
        pdf.setTitle(title)
        pdf.setAuthor(author)
        pdf.setKeywords(keywords)
            
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
            
            page_iter = document_model.iter_next(page_iter)
            
        # Save complete PDF
        pdf.save()
            
        assert os.path.exists(save_model.filename), \
            'Final PDF file was not created by ReportLab.'
                    
        page_iter = document_model.get_iter_first()
        while page_iter:
            # TODO: try block
            os.remove(document_model.get_value(page_iter, 0).path)
            page_iter = document_model.iter_next(page_iter)
            
        document_model.clear()
        
        save_view['pdf_dialog'].window.set_cursor(None)
        save_view['pdf_dialog'].hide()
        
    # PUBLIC METHODS
    
    def run(self):
        """Run the save dialog."""
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        
        save_view['save_dialog'].set_current_folder(save_model.save_path)
        save_view['save_dialog'].set_current_name('')
        save_view.run()
        
    # UTILITY METHODS
    
    def _save_pdf(self):
        """Run the dialog to get PDF metadata."""
        save_model = self.application.get_save_model()
        save_view = self.application.get_save_view()
        
        title = save_model.filename.split('/')[-1][0:-4]
        author = save_model.author
        keywords = ''
        
        save_view['title_entry'].set_text(title)
        save_view['author_entry'].set_text(author)
        save_view['keywords_entry'].set_text(keywords)
        
        save_view['pdf_dialog'].run()
    
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