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
import gtk
from gtkmvc.model import ListStoreModel

from models.page import PageModel

class DocumentModel(ListStoreModel):
    """
    Represents a multi-page document in the process of being scanned.
    This is represented as a liststore of L{PageModel} objects so that it can
    be fed into a treeview to provide an outline of the document.
    """
    
    def __init__(self):
        """
        Constructs the DocumentModel.
        """
        ListStoreModel.__init__(self, gobject.TYPE_PYOBJECT)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Create a blank page to use as a placeholder when none have been
        # scanned.
        self.blank_page = PageModel()
        
        self.log.debug('Created.')
    
    # PROPERTY CALLBACKS
        
    def property_thumbnail_pixbuf_value_change(self, model, old_value, new_value):
        """
        Searches through the liststore for the PageModel that has been
        changed and issues its row's row_changed event so that its display
        will be updated.
        """
        iter = self.get_iter_first()
        
        while iter:
            if self.get_value(iter, 0) == model:
                self.row_changed(self.get_path(iter), iter)
                return
                
            iter = self.iter_next(iter)
            
    # PUBLIC METHODS
        
    def append_page(self, page_model):
        """
        Adds a page to the end of the document.
        """
        self.append([page_model])
        page_model.register_observer(self)