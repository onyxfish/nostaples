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

class KeywordsCompletionEntry(gtk.Entry):
    """
    A specialized gtk.Entry widget which integrates completion support
    for tags or keywords stored in a gtk.ListStore.
    
    Inspired by 
    U{http://www.oluyede.org/blog/2005/04/25/pygtk-entrymulticompletion/}.
    """
    def __init__(self):
        """
        Construct the widget and setup its completion handler.
        """
        gtk.Entry.__init__(self) 
        
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(gtk.ListStore(gobject.TYPE_STRING))
        self.completion.set_text_column(0)
        self.completion.set_match_func(self.matching_function, None)
        self.completion.set_popup_completion(True)
        self.completion.connect("match-selected", self.on_match_selected) 
        
        self.set_completion(self.completion)
        self.connect("activate", self.on_entry_activate)

    def matching_function(self, completion, key_string, iter, data):
        """
        Match partial keywords.
        
        For an explanation of why match_test is validated, see here:
        U{http://faq.pygtk.org/index.py?file=faq13.028.htp&req=show}
        """
        model = self.completion.get_model()
        match_test = model[iter][0]
        
        # Attempting to match a row which has been created,
        # but not set.
        if not match_test:
            return False
        
        # If nothing has been keyed, no match
        if len(key_string) == 0:
            return False
        
        # If the last character was a space then no match
        if key_string[-1] == " ":
            return False
        
        # Get characters keyed since last space
        word = key_string.split()[-1]
        
        return match_test.startswith(word)

    def on_match_selected(self, completion, model, iter):
        """
        Insert matches into text without overwriting existing
        keywords.
        """
        current_text = self.get_text()
        
        # If no other words, then the new word is the only text
        if len(current_text) == 0 or current_text.find(" ") == -1:
            current_text = "%s " % (model[iter][0])
        # Append new word to existing words
        else:
            current_text = " ".join(current_text.split()[:-1])
            current_text = "%s %s " % (current_text, model[iter][0])
            
        self.set_text(current_text)
        self.set_position(-1)

        # stop the event propagation
        return True
        
    def on_entry_activate(self, entry):
        """
        Move to next keyword.
        """
            #if len(main_model.available_scanners) > 0:
        self.set_text("%s " % self.get_text())
        self.set_position(-1)
        print 'NOT FOUND'
        
    def get_liststore(self):
        """
        Return the gtk.ListStore containing the keywords.
        """
        return self.completion.get_model()

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
    
        print 'NOT FOUND'
    @type combobox: gtk.ComboBox
    @param combobox: The combobox to be setup.
    
    @type item_list: list of strings.
    @param item_list: The items to add to the menu box.
    
    @type selection: string
    @param selection: The item to be selected by default.
    """
    liststore = gtk.ListStore(type(item_list[0]))
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

def write_combobox(combobox, value):
    """
    Selects a value in a simple combobox.
    
    @type combobox: gtk.ComboBox
    @param combobox: The combobox to set.
    """
    liststore = combobox.get_model()
    
    row_iter = liststore.get_iter_first()
    
    while row_iter:            
        if liststore.get_value(row_iter, 0) == value:
            combobox.set_active_iter(row_iter)
            break
        
        row_iter = liststore.iter_next(row_iter)
        
    if row_iter == None:
        raise ValueError