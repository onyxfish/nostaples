#!/usr/env/python

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
This module contains global configuration constants that are not likely to 
change often as well as enumeration-like state constants.
'''

import os

from reportlab.lib.pagesizes import A0, A1, A2, A3, A4, A5, A6, \
    B0, B1, B2, B3, B4, B5, B6, LETTER, LEGAL, ELEVENSEVENTEEN

PAGESIZES = {'A0' : A0, 
                        'A1' : A1, 
                        'A2' : A2, 
                        'A3' : A3,
                        'A4' : A4, 
                        'A5' : A5, 
                        'A6' : A6,
                        'B0' : B0, 
                        'B1' : B1, 
                        'B2' : B2, 
                        'B3' : B3, 
                        'B4' : B4, 
                        'B5' : B5, 
                        'B6' : B6,
                        'LETTER' : LETTER, 
                        'LEGAL' : LEGAL, 
                        'ELEVENSEVENTEEN' : ELEVENSEVENTEEN}
                        
DEFAULT_ACTIVE_SCANNER = ''
DEFAULT_SCAN_MODE = 'Color'
DEFAULT_SCAN_RESOLUTION = '75'

DEFAULT_THUMBNAIL_SIZE = 128

STATUSBAR_BASE_CONTEXT_ID = 0
STATUSBAR_PREVIEW_CONTEXT_ID = 1
STATUSBAR_SCAN_CONTEXT_ID = 2
STATUSBAR_SCANNER_STATUS_CONTEXT_ID = 3

LOG_PATH = os.path.expanduser('~/.nostaples')
LOG_NAME = 'nostaples.log'

SCAN_CANCELLED = -1
SCAN_FAILURE = 0
SCAN_SUCCESS = 1

GCONF_FOLDER = "/apps/nostaples"
