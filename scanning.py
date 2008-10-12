#!/usr/env/python

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

import os
import commands
import re

SCAN_CANCELLED = -1
SCAN_FAILURE = 0
SCAN_SUCCESS = 1

def get_available_scanners():
    update_command = 'scanimage -f "%d=%v %m;"'
    print 'Updating available scanners with command: "%s".' % \
        update_command
    output = commands.getoutput(update_command)

    scanner_dict = {}
    scanner_list = re.findall('(.*?)=(.*?)[;|$]', output)
    
    for value, key in scanner_list:
        scanner_dict[key] = value
        
    return scanner_dict
    
def get_scanner_options(scanner):
    update_command = ' '.join(['scanimage --help -d',  scanner])
    print 'Updating scanner options with command: "%s".' % \
        update_command
    output = commands.getoutput(update_command)

    try:
        mode_list = re.findall('--mode (.*) ', output)[0].split('|')
    except IndexError:
        print 'Could not parse scan modes or no modes available for \
            device "%s".' % scanner
        mode_list = None
        
    try:
        resolution_list = re.findall('--resolution (.*)dpi ', output)[0].split('|')
    except IndexError:
        print 'Could not parse resolutions or no resolutions available for \
            device "%s".' % scanner
        resolution_list = None
    
    return (mode_list, resolution_list)

def scan_to_file(scanner, mode, resolution, filename):    
    scan_program = 'scanimage --format=pnm'
    mode_flag = ' '.join(['--mode', mode])
    resolution_flag = ' '.join(['--resolution', resolution])
    scanner_flag = ' '.join(['-d', scanner])
    output_file = '>%s' % filename
    scan_command = ' '.join(
        [scan_program, mode_flag, resolution_flag, scanner_flag, output_file])
    
    print 'Scanning with command: "%s".' % scan_command
    output = commands.getoutput(scan_command)
    
    if not os.path.exists(filename):
        print 'Scan failed: file %s not created.' % filename
        return SCAN_FAILURE
    
    if os.stat(filename).st_size <= 0:
        print 'Scan failed: file %s is empty.' % filename
        os.remove(filename)
        return SCAN_FAILURE
            
    print 'Scan complete'
    return SCAN_SUCCESS
