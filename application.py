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
This module holds NoStaples' main method which handles
the instantiation of MVC objects and then starts the gtk
main loop.
"""

import logging.config
import os
import sys
import threading

import gtk

import constants

from models.main import MainModel
from views.main import MainView
from controllers.main import MainController


def run():
    if not os.path.exists(constants.TEMP_IMAGES_DIRECTORY):
        os.mkdir(constants.TEMP_IMAGES_DIRECTORY)
    
    logging.config.fileConfig(constants.LOGGING_CONFIG)
    
    main_model = MainModel()
    main_controller = MainController(main_model)
    main_view = MainView(main_controller)
    
    gtk.gdk.threads_init()
    gtk.main()
