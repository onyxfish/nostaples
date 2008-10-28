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
from utils.gui import setup_combobox

class PreferencesView(View):
    """
    TODO
    """

    def __init__(self, controller, parent):
        View.__init__(
            self, controller, constants.GLADE_CONFIG, 'preferences_dialog', 
            parent, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Setup controls which can not be configured in Glade
        setup_combobox(
            self['preview_mode_combobox'], 
            [constants.PREVIEW_MODE_NEAREST,
                constants.PREVIEW_MODE_BILINEAR, 
                constants.PREVIEW_MODE_BICUBIC, 
                constants.PREVIEW_MODE_ANTIALIAS], 
            constants.PREVIEW_MODE_ANTIALIAS)
        
        controller.register_view(self)
        
        self.log.debug('Created.')
