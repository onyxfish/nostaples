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
TODO
"""

import logging

import gtk
from gtkmvc.view import View

import constants

class ThumbnailsView(View):
    """
    TODO
    """

    def __init__(self, controller):
        View.__init__(
            self, controller, None, None, None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        self['thumbnails_tree_view'] = gtk.TreeView()
        self['thumbnails_column'] = gtk.TreeViewColumn(None)
        self['thumbnails_cell'] = gtk.CellRendererPixbuf()
        self['thumbnails_column'].set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
#        self.thumbnails_column.set_fixed_width(
#            self.app.state_manager['thumbnail_size'])
        self['thumbnails_column'].set_fixed_width(128)
        self['thumbnails_tree_view'].append_column(self['thumbnails_column'])
        self['thumbnails_column'].pack_start(self['thumbnails_cell'], True)
        self['thumbnails_column'].set_attributes(
            self['thumbnails_cell'], pixbuf=0)
        self['thumbnails_tree_view'].get_selection().set_mode(
            gtk.SELECTION_SINGLE)
        self['thumbnails_tree_view'].set_headers_visible(False)
        self['thumbnails_tree_view'].set_property('can-focus', False)
        
        self['thumbnails_tree_view'].set_reorderable(True)
#        self.thumbnails_list_store.connect(
#            'row-inserted', self._on_thumbnails_list_store_row_inserted)
#        self.thumbnails_tree_view.get_selection().connect(
#            'changed', self._on_thumbnails_tree_selection_changed)
        
        controller.register_view(self)
        
        self.log.debug('Created.')
