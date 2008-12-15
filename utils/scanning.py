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

import commands
import logging
import os
import re
import tempfile
import threading

import gobject

import constants

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
    
    This class is based on an example by John Stowers:
    U{http://www.johnstowers.co.nz/blog/index.php/tag/pygtk/}
    """
    __gsignals__ =  {
            "finished": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
            }
    
    def __init__(self, main_model):
        """
        Initialize the thread.
        """
        IdleObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.model = main_model
        
        self.log.debug('Created.')
    
    def run(self):
        """
        Queries SANE for a list of connected scanners and updates
        the list of available scanners from the results.
        """
        update_command = 'scanimage -f "%d=%v %m;"'
        self.log.debug(
            'Updating available scanners with command: "%s".' % \
            update_command)
        output = commands.getoutput(update_command)

        results = re.findall('(.*?)=(.*?)[;|$]', output)
        scanner_list = []
        
        for sane_name, display_name in results:
            scanner_already_in_list = False
            
            # Check if the scanner has already been connected, if so
            # use existing instance so settings are not lost.
            for scanner in self.model.available_scanners:
                if scanner[1] == sane_name:
                    scanner_already_in_list = True
                    scanner_list.append(scanner)
            
            if not scanner_already_in_list:
                scanner_list.append((display_name, sane_name))
        
        # NB: We callback with the lists so that they can updated on the main thread
        self.emit("finished", scanner_list)        

class ScanningThread(IdleObject, threading.Thread):
    """
    Responsible for scanning a page and emitting status
    callbacks on the main thread.
    
    This thread should treat its reference to the ScanningModel
    as read-only.  That way we don't have to worry about making
    the Model thread-safe.
    
    This class is based on an example by John Stowers:
    U{http://www.johnstowers.co.nz/blog/index.php/tag/pygtk/}
    """
    __gsignals__ =  {
            "succeeded": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
            "failed": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
            }
    
    def __init__(self, main_model):
        """
        Initialize the thread and get a tempfile name that
        will house the scanned image.
        """
        IdleObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.model = main_model
        self.path = tempfile.mktemp()
        
        self.log.debug('Created targeting temp file %s.' % self.path)
    
    def run(self):
        """
        Scan a page and emit status callbacks.
        """
        scan_program = 'scanimage --format=pnm'
        mode_flag = ' '.join(['--mode', self.model.active_mode])
        resolution_flag = ' '.join(['--resolution', self.model.active_resolution])
        scanner_flag = ' '.join(['-d', self.model.active_scanner[1]])
        output_file = '>%s' % self.path
        scan_command = ' '.join(
            [scan_program, mode_flag, resolution_flag, scanner_flag, output_file])
        
        self.log.info(
            'Scanning with command: "%s".' % scan_command)
        output = commands.getoutput(scan_command)
        
        # TODO: check output for errors?
        
        if not os.path.exists(self.path):
            self.log.error(
                'Failed: temp file %s not created.' % self.path)
            self.emit("failed")
            return
        
        if os.stat(self.path).st_size <= 0:
            self.log.error(
                'Failed: temp file %s is empty.' % self.path)
            self.emit("failed")
            return

        self.emit("succeeded", self.path)
        
class UpdateScannerOptionsThread(IdleObject, threading.Thread):
    """
    Responsible for getting an up-to-date list of valid scanner options
    and passing it back to the main thread.
    
    This thread should treat its reference to the ScanningModel
    as read-only.  That way we don't have to worry about making
    the Model thread-safe.
    
    This class is based on an example by John Stowers:
    U{http://www.johnstowers.co.nz/blog/index.php/tag/pygtk/}
    """
    __gsignals__ =  {
            "finished": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
            }
    
    def __init__(self, main_model):
        """
        Initialize the thread.
        """
        IdleObject.__init__(self)
        threading.Thread.__init__(self)
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.model = main_model
        
        self.log.debug('Created.')
    
    def run(self):
        """
        Queries SANE for a list of available options for the specified scanner.    
        """
        print self.model.active_scanner
        update_command = ' '.join(['scanimage --help -d',  self.model.active_scanner[1]])
        self.log.debug(
            'Updating scanner options with command: "%s".' % \
            update_command)
        output = commands.getoutput(update_command)
        
        # TODO: check that scanner was found

        try:
            mode_list = re.findall('--mode (.*) ', output)[0].split('|')
        except IndexError:
            self.log.warn(
                'Could not parse scan modes or no modes available for \
                device "%s".' % self.model.active_scanner[0])
            mode_list = []
            
        try:
            resolution_list = re.findall('--resolution (.*)dpi ', output)[0].split('|')
        except IndexError:
            self.log.warn(
                'Could not parse resolutions or no resolutions available for \
                device "%s".' % self.model.active_scanner[0])
            resolution_list = []
        
        # NB: We callback with the lists so that they can updated on the main thread
        self.emit("finished", mode_list, resolution_list)