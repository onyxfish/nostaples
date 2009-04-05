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
This module contains global configuration constants that are not likely to 
change often as well as enumeration-like state constants.
'''

import os

import gtk
import Image
from reportlab.lib.pagesizes import A0, A1, A2, A3, A4, A5, A6, \
    B0, B1, B2, B3, B4, B5, B6, LETTER, LEGAL, ELEVENSEVENTEEN
    
VERSION = (0, 4, 0)

PAGESIZES_INCHES = {'A0' : (33.1, 46.8), 
                    'A1' : (23.4, 33.1), 
                    'A2' : (16.5, 23.4), 
                    'A3' : (11.7, 16.5),
                    'A4' : (8.3, 11.7), 
                    'A5' : (5.8, 8.3), 
                    'A6' : (4.1, 5.8),
                    'A7' : (2.9, 4.1),
                    'A8' : (2.0, 2.9),
                    'A9' : (1.5, 2.0),
                    'A10' : (1.0, 1.5),
                    'B0' : (39.4, 55.7), 
                    'B1' : (27.8, 39.4), 
                    'B2' : (19.7, 27.8), 
                    'B3' : (13.9, 19.7), 
                    'B4' : (9.8, 13.9), 
                    'B5' : (6.9, 9.8), 
                    'B6' : (4.9, 6.9),
                    'B7' : (3.5, 4.9),
                    'B8' : (2.4, 3.5),
                    'B9' : (1.7, 2.4),
                    'B10' : (1.2, 1.7),
                    'Letter' : (8.5, 11.0), 
                    'Legal' : (8.5, 14.0), 
                    'Junior Legal' : (8.0, 5.0),
                    'Ledger' : (17.0, 11.0),
                    'Tabloid' : (11.0, 17.0),
                    '3x5 Photo' : (3.0, 5.0),
                    '4x6 Photo' : (4.0, 6.0),
                    '5x7 Photo' : (5.0, 7.0),
                    '8x10 Photo' : (8.0, 10.0),
                    '11x14 Photo' : (11.0, 14.0)}

PAGESIZES_MM = {'A0' : (841.0, 1189.0), 
                    'A1' : (594.0, 841.0), 
                    'A2' : (420.0, 594.0), 
                    'A3' : (297.0, 420.0),
                    'A4' : (210.0, 297.0), 
                    'A5' : (148.0, 210.0), 
                    'A6' : (105.0, 148.0),
                    'A7' : (74.0, 105.0),
                    'A8' : (52.0, 74.0),
                    'A9' : (37.0, 52.0),
                    'A10' : (26.0, 37.0),
                    'B0' : (1000.0, 1414.0), 
                    'B1' : (707.0, 1000.0), 
                    'B2' : (500.0, 707.0), 
                    'B3' : (353.0, 500.0), 
                    'B4' : (250.0, 353.0), 
                    'B5' : (176.0, 250.0), 
                    'B6' : (125.0, 176.0),
                    'B7' : (88.0, 125.0),
                    'B8' : (62.0, 88.0),
                    'B9' : (44.0, 62.0),
                    'B10' : (31.0, 44.0),
                    'Letter' : (216.0, 279.0), 
                    'Legal' : (216.0, 356.0), 
                    'Junior Legal' : (203.2, 127.0),
                    'Ledger' : (432.0, 279.0),
                    'Tabloid' : (279.0, 43.0),
                    '3x5 Photo' : (76.0, 127.0),
                    '4x6 Photo' : (102.0, 152.0),
                    '5x7 Photo' : (127.0, 178.0),
                    '8x10 Photo' : (203.0, 254.0),
                    '11x14 Photo' : (279.0, 356.0)}

PAGESIZE_SORT_ORDER = ['A0', 
                        'A1', 
                        'A2',
                        'A3',
                        'A4', 
                        'A5', 
                        'A6',
                        'A7',
                        'A8',
                        'A9',
                        'A10',
                        'B0', 
                        'B1', 
                        'B2', 
                        'B3', 
                        'B4', 
                        'B5', 
                        'B6',
                        'B7',
                        'B8',
                        'B9',
                        'B10',
                        'Letter', 
                        'Legal', 
                        'Junior Legal',
                        'Ledger',
                        'Tabloid',
                        '3x5 Photo',
                        '4x6 Photo',
                        '5x7 Photo',
                        '8x10 Photo',
                        '11x14 Photo']

DEFAULT_SHOW_TOOLBAR = True
DEFAULT_SHOW_STATUSBAR = True
DEFAULT_SHOW_THUMBNAILS = True
DEFAULT_SHOW_ADJUSTMENTS = False
DEFAULT_ROTATE_ALL_PAGES = False
DEFAULT_ACTIVE_SCANNER = ''
DEFAULT_SCAN_MODE = 'Color'
DEFAULT_SCAN_RESOLUTION = '75'
DEFAULT_PAGE_SIZE = 'A4'
DEFAULT_SAVE_PATH = ''
DEFAULT_AUTHOR = os.getenv('LOGNAME')
DEFAULT_SAVED_KEYWORDS = []
DEFAULT_PREVIEW_MODE = 'Bilinear (Default)'
DEFAULT_THUMBNAIL_SIZE = 128
DEFAULT_SHOW_DOCUMENT_METADATA = True
DEFAULT_BLACKLISTED_SCANNERS = []
DEFAULT_TOOLBAR_STYLE = 'System Default'

THUMBNAILS_SCALING_MODE = Image.ANTIALIAS

PREVIEW_ZOOM_MAX = 5.0
PREVIEW_ZOOM_MIN = 1.0
PREVIEW_ZOOM_STEP = 0.5

MAX_VALID_OPTION_VALUES = 11

SCAN_CANCELLED = -1
SCAN_FAILURE = 0
SCAN_SUCCESS = 1

RESPONSE_BLACKLIST_DEVICE = 1

GCONF_DIRECTORY = '/apps/nostaples'
GCONF_TUPLE_SEPARATOR = '|'
GCONF_LIST_SEPARATOR = '^'

# TODO: rename to CONFIG_DIRECTORY
APP_DIRECTORY = os.path.expanduser('~/.nostaples')
LOGGING_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.config')
GUI_DIRECTORY = os.path.join(os.path.dirname(__file__), 'gui')

PREVIEW_MODES = \
{
    'Nearest (Fastest)': gtk.gdk.INTERP_NEAREST,
    'Tiles': gtk.gdk.INTERP_TILES,
    'Bilinear (Default)': gtk.gdk.INTERP_BILINEAR,
    'Antialias (Smoothest)': gtk.gdk.INTERP_HYPER
}
 
PREVIEW_MODES_LIST = \
[
    'Nearest (Fastest)',
    'Tiles',
    'Bilinear (Default)',
    'Antialias (Smoothest)'
]

THUMBNAIL_SIZE_LIST = \
[
    32,
    64,
    128,
    256
]

TOOLBAR_STYLES = \
{
    'System Default': None,
    'Icons Only': gtk.TOOLBAR_ICONS,
    'Text Only': gtk.TOOLBAR_TEXT,
    'Icons and Text (Stacked)': gtk.TOOLBAR_BOTH,
    'Icons and Text (Side by side)': gtk.TOOLBAR_BOTH_HORIZ
}

TOOLBAR_STYLES_LIST = \
[
    'System Default',
    'Icons Only',
    'Text Only',
    'Icons and Text (Stacked)',
    'Icons and Text (Side by side)'
]