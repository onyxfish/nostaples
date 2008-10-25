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
This module holds the Model for a single scanned page.
'''

import logging

from gtkmvc.model import Model

class PageModel(Model):
    '''
    TODO
    '''
    __properties__ = \
    {
        'path' : '',
        'rotation' : 0,
        'brightness' : 1.0,
        'contrast' : 1.0,
        'sharpness' : 1.0,
        'resolution' : 75,
        'pixbuf' : None,
    }

    def __init__(self):
        Model.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.log.debug('Created.')
