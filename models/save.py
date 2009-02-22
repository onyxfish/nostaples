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
This module holds the SaveModel, which manages data related to
saving documents.
"""

import logging

from gtkmvc.model import Model

from nostaples import constants
import nostaples.utils.properties

class SaveModel(Model):
    """
    Handles data the metadata associated with saving documents.
    """
    __properties__ = \
    {
        'save_path' : '',
        'title' : '',
        'author' : '',
        'keywords' : '',
        
        'show_document_metadata' : True,
        
        'filename' : '',
    }

    def __init__(self, application):
        """
        Constructs the SaveModel.
        """
        self.application = application
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')
        
    def load_state(self):
        """
        Load persisted state from the self.state_manager.
        """
        state_manager = self.application.get_state_manager()
        
        self.save_path = state_manager.init_state(
            'save_path', constants.DEFAULT_SAVE_PATH, 
            nostaples.utils.properties.PropertyStateCallback(self, 'save_path'))
        
        self.author = state_manager.init_state(
            'author', constants.DEFAULT_AUTHOR, 
            nostaples.utils.properties.PropertyStateCallback(self, 'author'))
        
        self.show_document_metadata = state_manager.init_state(
            'show_document_metadata', constants.DEFAULT_SHOW_DOCUMENT_METADATA, 
            nostaples.utils.properties.PropertyStateCallback(self, 'show_document_metadata'))
        
    # PROPERTY SETTERS
    
    set_prop_save_path = nostaples.utils.properties.StatefulPropertySetter(
        'save_path')
    set_prop_author = nostaples.utils.properties.StatefulPropertySetter(
        'author')
    set_prop_show_document_metadata = nostaples.utils.properties.StatefulPropertySetter(
        'show_document_metadata')