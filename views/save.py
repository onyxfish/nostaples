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
This module holds the MainView which exposes the application's main 
window.
"""

import logging
import os

import gtk
from gtkmvc.view import View

from nostaples import constants
import nostaples.utils.gui

class SaveView(View):
    """
    Exposes the application's main window.
    """

    def __init__(self, application):
        """
        Constructs the MainView, including setting up controls that could
        not be configured in Glade and constructing sub-views.
        """
        self.application = application
        save_dialog_glade = os.path.join(
            constants.GUI_DIRECTORY, 'save_dialog.glade')
        View.__init__(
            self, self.application.get_save_controller(), 
            save_dialog_glade, 'save_dialog', 
            None, False)
            
        self.log = logging.getLogger(self.__class__.__name__)
        
        # Can't do this in constructor as main_view has multiple
        # top widgets
        self['save_dialog'].set_transient_for(
            self.application.get_main_view()['scan_window'])
        
        # Setup filename filter
        filename_filter = gtk.FileFilter()
        filename_filter.set_name('PDF Files')
        filename_filter.add_mime_type('application/pdf')
        filename_filter.add_pattern('*.pdf')
        self['save_dialog'].add_filter(filename_filter)
        
        # Setup custom control
        self['keywords_entry'] = nostaples.utils.gui.KeywordsCompletionEntry()
        self['keywords_hbox'].pack_start(self['keywords_entry'])
        self['keywords_hbox'].reorder_child(self['keywords_entry'], 1)
        self['keywords_entry'].show()
        
        model = self['keywords_entry'].get_liststore()
        for word in ["abc", "def", "ghi", "jkl", "mno", "pqr", "stu", "vwx", "yz"]:
            model.append([word])
        
        self.application.get_save_controller().register_view(self)
        
        self.log.debug('Created.')
        
    def run(self):
        """Run the modal save dialog."""
        self['save_dialog'].run()