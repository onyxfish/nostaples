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
This module holds utility methods for populating and
reading from pygtk controls.
"""

import gtk
import gobject

def flush_pending_events():
    """
    This event flushes any pending idle operations
    without returning to the GTK main loop.
    
    It can be used to ensure that all GUI updates have
    been processed prior to a long-running operation.
    
    Do NOT use if any calls to gobject.idle_add have been
    made as those idle methods will cause an infinite
    loop.
    """
    while gtk.events_pending() :
        gtk.main_iteration(False)

def setup_combobox(combobox, item_list, selection):
    """
    Sets up a simple combobox.
    
    @type combobox: gtk.ComboBox
    @param combobox: The combobox to be setup.
    
    @type item_list: list of strings.
    @param item_list: The items to add to the menu box.
    
    @type selection: string
    @param selection: The item to be selected by default.
    """
    liststore = gtk.ListStore(gobject.TYPE_STRING)
    combobox.clear()
    combobox.set_model(liststore)
    cell = gtk.CellRendererText()
    combobox.pack_start(cell, True)
    combobox.add_attribute(cell, 'text', 0)  

    for item in item_list:
        liststore.append([item])
        
    try:
        index = item_list.index(selection)
    except ValueError:
        index = 0

    combobox.set_active(index)
    
def read_combobox(combobox):
    """
    Reads the currently selected item from a
    simple combobox.
    
    @type combobox: gtk.ComboBox
    @param combobox: The combobox to read from.
    """
    liststore = combobox.get_model()
    active = combobox.get_active()
    
    if active < 0:
        return None
        
    return liststore[active][0]