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

class SaveModel(Model):
    """
    Handles data the metadata associated with saving documents.
    """
    __properties__ = \
    {
         # TODO
        'save_path' : '',
        'filename' : '',
        'author' : 'TODO author',
    }

    def __init__(self):
        """
        Constructs the SaveModel.
        """
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')