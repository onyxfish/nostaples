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
This module holds the DocumentModel, which represents a multi-page
document in the process of being scanned.
"""

import logging

import gobject
from gtkmvc.model import ListStoreModel

class DocumentModel(ListStoreModel):
    """
    Represents a multi-page document in the process of being scanned.
    This is represented as a liststore of L{PageModel} objects so that it can
    be fed into a treeview to provide an outline of the document.
    """
    __properties__ = \
    {
        'count' : 0,
        'adjust_all_pages' : False,
        'manually_updating_row' : False,
    }
    
    def __init__(self, application):
        """
        Constructs the DocumentModel.
        """
        self.application = application
        ListStoreModel.__init__(self, gobject.TYPE_PYOBJECT)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')
    
    # PROPERTY CALLBACKS
        
    def property_thumbnail_pixbuf_value_change(self, model, old_value, new_value):
        """
        Searches through the liststore for the PageModel that has been
        changed and issues its row's row_changed event so that its display
        will be updated.
        """
        search_iter = self.get_iter_first()
        
        while search_iter:
            if self.get_value(search_iter, 0) == model:
                self.row_changed(self.get_path(search_iter), search_iter)
                return
                
            search_iter = self.iter_next(search_iter)
            
    # PUBLIC METHODS
            
    def append(self, page_model):
        """Adds a page to the end of the document."""
        super(DocumentModel, self).append([page_model])
        page_model.register_observer(self)
        self.count += 1
        
    def prepend(self, page_model):
        """Adds a page to the beginning of the document."""
        super(DocumentModel, self).prepend([page_model])
        page_model.register_observer(self)
        self.count += 1
        
    def insert(self, position, page_model):
        """Insert a page in the doucument at the specified position."""
        super(DocumentModel, self).insert(position, [page_model])
        page_model.register_observer(self)
        self.count += 1
    
    def insert_before(self, loc_iter, page_model):
        """Insert a page in the doucument before the iter."""
        super(DocumentModel, self).insert_before(loc_iter, [page_model])
        page_model.register_observer(self)
        self.count += 1
    
    def insert_after(self, loc_iter, page_model):
        """Insert a page in the doucument after the iter."""
        super(DocumentModel, self).insert_after(loc_iter, [page_model])
        page_model.register_observer(self)
        self.count += 1
        
    def remove(self, loc_iter):
        """Remove a page from the doucument."""
        self.get_value(loc_iter, 0).unregister_observer(self)
        super(DocumentModel, self).remove(loc_iter)
        self.count -= 1
        
    def clear(self):
        """Remove all pages from the document."""
        for row in self:
            row[0].unregister_observer(self)
        super(DocumentModel, self).clear()
        self.count = 0