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
This module holds the MainModel, which manages general application
data. 
"""

import logging

from gtkmvc.model import Model

from models.document import DocumentModel
from models.page import PageModel
from models.preferences import PreferencesModel
from models.scanner import ScannerModel

class MainModel(Model):
    """
    Handles data all data not specifically handled by another Model 
    (e.g. the state of the main application window).
    """
    __properties__ = \
    {
        'show_toolbar' : True,
        'show_statusbar' : True,
        'show_thumbnails' : True,
        'available_scanners' : [],
        'active_scanner' : None,
        'is_scanner_in_use' : False,
    }

    def __init__(self):
        """
        Constructs the MainModel, as well as necessary sub-models.
        """
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Sub-models
        self.document_model = DocumentModel()
        self.preferences_model = PreferencesModel()
        
        self.null_scanner = ScannerModel('Null Scanner', '')
        
        self.log.debug('Created.')
