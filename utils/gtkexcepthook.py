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

# This module is based on:

# gtkexcepthook.py

# (c) 2003 Gustavo J A M Carneiro gjc at inescporto.pt
#     2004-2005 Filip Van Raemdonck

# http://www.daa.com.au/pipermail/pygtk/2003-August/005775.html
# Message-ID: <1062087716.1196.5.camel@emperor.homelinux.net>
#     "The license is whatever you want."

"""
This module contains a replacement sys.excepthook which informs the
user of the error via a GTK dialog and allows them to control
whether or not the application exits.
"""

from cStringIO import StringIO
import inspect
import linecache
import logging
import pydoc
import sys
import traceback

import gtk
import pango
import pygtk
pygtk.require ('2.0')

def lookup (name, frame, lcls):
    """
    Find the value for a given name in a given frame.
    
    This function is unmodified from Filip Van Raemdonck's
    version.
    """
    if name in lcls:
        return 'local', lcls[name]
    elif name in frame.f_globals:
        return 'global', frame.f_globals[name]
    elif '__builtins__' in frame.f_globals:
        builtins = frame.f_globals['__builtins__']
        if type (builtins) is dict:
            if name in builtins:
                return 'builtin', builtins[name]
        else:
            if hasattr (builtins, name):
                return 'builtin', getattr (builtins, name)
    return None, []

def analyse (exctyp, value, tb):
    """
    Create a text representation of an exception traceback.
    
    This function is unmodified from Filip Van Raemdonck's
    version.
    """
    import tokenize, keyword

    trace = StringIO()
    nlines = 3
    frecs = inspect.getinnerframes (tb, nlines)
    trace.write ('Traceback (most recent call last):\n')
    for frame, fname, lineno, funcname, context, cindex in frecs:
        trace.write ('  File "%s", line %d, ' % (fname, lineno))
        args, varargs, varkw, lcls = inspect.getargvalues (frame)

        def readline (lno=[lineno], *args):
            if args: print args
            try: return linecache.getline (fname, lno[0])
            finally: lno[0] += 1
        all, prev, name, scope = {}, None, '', None
        for ttype, tstr, stup, etup, line in tokenize.generate_tokens (readline):
            if ttype == tokenize.NAME and tstr not in keyword.kwlist:
                if name:
                    if name[-1] == '.':
                        try:
                            val = getattr (prev, tstr)
                        except AttributeError:
                            # XXX skip the rest of this identifier only
                            break
                        name += tstr
                else:
                    assert not name and not scope
                    scope, val = lookup (tstr, frame, lcls)
                    name = tstr
                if val:
                    prev = val
                #print '  found', scope, 'name', name, 'val', val, 'in', prev, 'for token', tstr
            elif tstr == '.':
                if prev:
                    name += '.'
            else:
                if name:
                    all[name] = (scope, prev)
                prev, name, scope = None, '', None
                if ttype == tokenize.NEWLINE:
                    break

        trace.write (funcname +
          inspect.formatargvalues (args, varargs, varkw, lcls, formatvalue=lambda v: '=' + pydoc.text.repr (v)) + '\n')
        trace.write (''.join (['    ' + x.replace ('\t', '  ') for x in filter (lambda a: a.strip(), context)]))
        if len (all):
            trace.write ('  variables: %s\n' % str (all))

    trace.write ('%s: %s' % (exctyp.__name__, value))
    return trace

def _gtkexcepthook(exception_type, instance, traceback):
    """
    Display a GTK dialog informing the user that an unhandled
    exception has occurred.  Log the exception and provide the
    option to continue or quit.

    TODO: Should have a way to report bugs.
    """
    trace_log = trace = analyse(exception_type, instance, traceback)
    
    log = logging.getLogger("gtkexcepthook")
    log.error("%s caught.  Traceback follows \n%s" % 
        (exception_type, trace_log.getvalue()))
    
    dialog = gtk.MessageDialog(
        parent=None, flags=0, type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_NONE)
    dialog.set_title("")
    
    # TODO: is this needed?
    if gtk.check_version (2, 4, 0) is not None:
        dialog.set_has_separator (False)

    primary = "<big><b>An unhandled exception has been logged.</b></big>"
    secondary = "It may be possible to continue normally, or you may choose to exit NoStaples and restart."

    dialog.set_markup(primary)
    dialog.format_secondary_text(secondary)

    dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
    dialog.add_button(gtk.STOCK_QUIT, 1)

    response = dialog.run()

    if response == 1 and gtk.main_level() > 0:
        gtk.main_quit()
    else:
        pass

    dialog.destroy()

sys.excepthook = _gtkexcepthook