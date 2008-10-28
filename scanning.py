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

import logging
import os
import commands
import re

import constants

class ScanningService():
    """
    Provides SANE-based scanning services to the application.
    This class is stateless.
    """
    
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('Created.')

    def get_available_scanners(self):
        """
        Queries SANE for a list of connected scanners.
        
        @return: A dictionary of available scanners in the format::
            
            dict[human_readable_name] = sane_backend_descriptor
        """
        update_command = 'scanimage -f "%d=%v %m;"'
        self.log.debug(
            'Updating available scanners with command: "%s".' % \
            update_command)
        output = commands.getoutput(update_command)

        scanner_dict = {}
        scanner_list = re.findall('(.*?)=(.*?)[;|$]', output)
        
        for value, key in scanner_list:
            scanner_dict[key] = value
            
        return scanner_dict
        
    def get_scanner_options(self, scanner):
        """
        Queries SANE for a list of available options for the specified scanner.
        
        @param scanner: A connected scanner.
        @type scanner: A string containing a SANE backend descriptor.
        
        @return: A tuple containing the following lists:
            - A list of valid scan modes ('Gray', 'Color', etc).
            - A list of valid scan resolutions ('75', '150', etc).        
        """
        update_command = ' '.join(['scanimage --help -d',  scanner])
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
                device "%s".' % scanner)
            mode_list = None
            
        try:
            resolution_list = re.findall('--resolution (.*)dpi ', output)[0].split('|')
        except IndexError:
            self.log.warn(
                'Could not parse resolutions or no resolutions available for \
                device "%s".' % scanner)
            resolution_list = None
        
        return (mode_list, resolution_list)

    def scan_to_file(self, scanner, mode, resolution, path):
        """
        Scans an image to a file using SANE's scanimage utility.
        
        @param scanner: A connected scanner.
        @type scanner: A string containing a SANE backend descriptor.
        
        @param mode: A scan mode.        
        @param resolution: A scan resolution.
        
        @param path: A location and filename at which to save the scanned 
            image.
            
        @return: L{constants.SCAN_FAILURE} or 
            L{constants.SCAN_SUCCESS}.
        """
        scan_program = 'scanimage --format=pnm'
        mode_flag = ' '.join(['--mode', mode])
        resolution_flag = ' '.join(['--resolution', resolution])
        scanner_flag = ' '.join(['-d', scanner])
        output_file = '>%s' % path
        scan_command = ' '.join(
            [scan_program, mode_flag, resolution_flag, scanner_flag, output_file])
        
        self.log.info(
            'Scanning with command: "%s".' % scan_command)
        output = commands.getoutput(scan_command)
        
        # TODO: check output for errors?
        
        if not os.path.exists(path):
            self.log.error(
                'Scan failed: file %s not created.' % path)
            return constants.SCAN_FAILURE
        
        if os.stat(path).st_size <= 0:
            self.log.error(
                'Scan failed: file %s is empty.' % path)
            os.remove(path)
            return constants.SCAN_FAILURE

        return constants.SCAN_SUCCESS
