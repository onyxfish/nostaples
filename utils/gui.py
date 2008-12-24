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
TODO
'''

import gtk
import gobject

def setup_combobox(combobox, item_list, selection):
    '''
    A short-cut for setting up simple comboboxes.
    '''
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
    '''
    A short-cut for reading from simple comboboxes.
    '''
    liststore = combobox.get_model()
    active = combobox.get_active()
    
    if active < 0:
        return None
        
    return liststore[active][0]
