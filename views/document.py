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
This module holds the DocumentView which exposes the document being
scanned as a thumbnail list.
"""

import logging
import os

import gtk
from gtkmvc.view import View

from nostaples import constants

class DocumentView(View):
    """
    Exposes the document being scanned as a thumbnail list.
    """

    def __init__(self, application):
        """
        Constructs the DocumentView, including setting up controls that could
        not be configured in Glade and constructing sub-views.
        """
        self.application = application
        document_view_glade = os.path.join(
            constants.GUI_DIRECTORY, 'document_view.glade')
        View.__init__(
            self, application.get_document_controller(), 
            document_view_glade, 'dummy_document_view_window', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Setup controls that could not be configured in Glade
        self['thumbnails_tree_view'] = gtk.TreeView()
        self['thumbnails_column'] = gtk.TreeViewColumn(None)
        self['thumbnails_cell'] = gtk.CellRendererPixbuf()
        self['thumbnails_column'].set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self['thumbnails_column'].set_fixed_width(constants.DEFAULT_THUMBNAIL_SIZE)
        self['thumbnails_tree_view'].append_column(self['thumbnails_column'])
        self['thumbnails_column'].pack_start(self['thumbnails_cell'], True)
        self['thumbnails_column'].set_cell_data_func(
            self['thumbnails_cell'], self.thumbnails_column_cell_data_func)
        self['thumbnails_tree_view'].get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self['thumbnails_tree_view'].set_headers_visible(False)
        self['thumbnails_tree_view'].set_property('can-focus', False)
        self['thumbnails_tree_view'].set_reorderable(True)

        self['thumbnails_scrolled_window'].add(self['thumbnails_tree_view'])
        
        self['thumbnails_context_menu'] = gtk.Menu()
        self['delete_menu_item'] = gtk.MenuItem('Delete')
        self['thumbnails_context_menu'].append(self['delete_menu_item'])
        self['thumbnails_context_menu'].show_all()

        # Dock sub-views
        page_view = self.application.get_page_view()
        page_view['page_view_table'].reparent(
            self['page_view_docking_viewport'])
        
        application.get_document_controller().register_view(self)
        
        self.log.debug('Created.')
        
    def thumbnails_column_cell_data_func(self, column, cell_renderer, document_model, iter):
        """
        Extracts the thumbnail pixbuf from the PageModel stored in the
        DocumentModel ListStore.
        """
        page_model = document_model.get_value(iter, 0)
        cell_renderer.set_property('pixbuf', page_model.thumbnail_pixbuf)
        
    def set_adjustments_sensitive(self, sensitive):
        """
        Set all adjustment controls sensitive or insensitive
        to user input.
        """
        self['brightness_label'].set_sensitive(sensitive)
        self['brightness_scale'].set_sensitive(sensitive)
        self['contrast_label'].set_sensitive(sensitive)
        self['contrast_scale'].set_sensitive(sensitive)
        self['sharpness_label'].set_sensitive(sensitive)
        self['sharpness_scale'].set_sensitive(sensitive)
        self['adjust_all_pages_check'].set_sensitive(sensitive)