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
This module contains those functions (in the form of Thread objects)
that interface with scanning hardware via SANE.
"""

import commands
import logging
import os
import re
import tempfile
import threading

import gobject

from nostaples import constants
import saneme

class IdleObject(gobject.GObject):
    """
    Override gobject.GObject to always emit signals in the main thread
    by emitting on an idle handler.
    
    This class is based on an example by John Stowers:
    U{http://www.johnstowers.co.nz/blog/index.php/tag/pygtk/}
    """
    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit,self,*args)
        
class UpdateAvailableScannersThread(IdleObject, threading.Thread):
    """
    Responsible for getting an updated list of available scanners
    and passing it back to the main thread.
    """
    __gsignals__ =  {
            "finished": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
            }
    
    def __init__(self, sane):
        """
        Initialize the thread.
        """
        IdleObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.sane = sane
        
        self.log.debug('Created.')
    
    def run(self):
        """
        Queries SANE for a list of connected scanners and updates
        the list of available scanners from the results.
        """
        self.log.debug('Updating available scanners.')

        try:
            devices = self.sane.get_device_list()
        except saneme.SaneOutOfMemoryError:
            # TODO
            raise
        except saneme.SaneUnknownError:
            # TODO
            raise
        
        # NB: We callback with the lists so that they can updated on the main thread
        self.emit("finished", devices)        

class ScanningThread(IdleObject, threading.Thread):
    """
    Responsible for scanning a page and emitting status
    callbacks on the main thread.
    
    This thread should treat its reference to the ScanningModel
    as read-only.  That way we don't have to worry about making
    the Model thread-safe.
    """
    __gsignals__ =  {
            "progress": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_INT)),
            "succeeded": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
            "failed": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
            }
    
    # TODO: add cancel event
    
    def __init__(self, sane_device, mode, resolution):
        """
        Initialize the thread and get a tempfile name that
        will house the scanned image.
        """
        IdleObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.sane_device = sane_device
        self.mode = mode
        self.resolution = resolution
        
        self.cancel_event = threading.Event()
        
    def progress_callback(self, scan_info, bytes_scanned):
        """
        Pass the progress information on the the main thread
        and cancel the scan if the cancel event has been set.
        """
        self.emit("progress", scan_info, bytes_scanned)
        
        if self.cancel_event.isSet():
            return True
        else:
            return False
    
    def run(self):
        """
        Scan a page and emit status callbacks.
        """
        assert self.sane_device.is_open()
        
        self.log.debug('Setting device options.')
        
        try:
            self.sane_device.options['mode'].value = self.mode
        # TODO
        except saneme.SaneReloadOptionsError:
            pass
        
        try:
            self.sane_device.options['resolution'].value = int(self.resolution)
        # TODO
        except saneme.SaneReloadOptionsError:
            pass
        
        self.log.debug('Beginning scan.')
        
        pil_image = None
        
        try:
            pil_image = self.sane_device.scan(self.progress_callback)
        # TODO: handle individual errors
        except saneme.SaneError:
            raise
        
        if self.cancel_event.isSet():
            self.emit("failed", "Scan cancelled")
        else:
            assert pil_image is not None
            self.emit("succeeded", pil_image)
        
class UpdateScannerOptionsThread(IdleObject, threading.Thread):
    """
    Responsible for getting an up-to-date list of valid scanner options
    and passing it back to the main thread.
    """
    __gsignals__ =  {
            "finished": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
            }
    
    def __init__(self, sane_device):
        """
        Initialize the thread.
        """
        IdleObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.sane_device = sane_device
        
        self.log.debug('Created.')
    
    def run(self):
        """
        Queries SANE for a list of available options for the specified scanner.    
        """
        assert self.sane_device.is_open()
        
        self.log.debug('Updating scanner options.')

        mode_list = self.sane_device.options['mode'].constraint_string_list
        resolution_list = [str(i) for i in self.sane_device.options['resolution'].constraint_word_list]
        
        # NB: We callback with the lists so that they can updated on the main thread
        self.emit("finished", mode_list, resolution_list)