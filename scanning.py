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
import threading
import re

SCAN_CANCELLED = -1
SCAN_FAILURE = 0
SCAN_SUCCESS = 1

def get_available_scanners():
	updateCmd = 'scanimage -f "%d=%v %m;"'
	print 'Updating available scanners with command: "%s"' % updateCmd
	output = commands.getoutput(updateCmd)

	scannerDict = {}
	scannerList = re.findall('(.*?)=(.*?)[;|$]', output)
	
	for v, k in scannerList:
		scannerDict[k] = v
		
	return scannerDict
	
def get_scanner_options(scanner):
	updateCmd = ' '.join(['scanimage --help -d',  scanner])
	print 'Updating scanner options with command: "%s"' % updateCmd
	output = commands.getoutput(updateCmd)

	try:
		modeList = re.findall('--mode (.*) ', output)[0].split('|')
	except IndexError:
		print 'Could not parse scan modes or no modes available for device "%s".' % scanner
		modeList = None
		
	try:
		resolutionList = re.findall('--resolution (.*)dpi ', output)[0].split('|')
	except IndexError:
		print 'Could not parse resolutions or no resolutions available for device "%s".' % scanner
		resolutionList = None
	
	return (modeList, resolutionList)

def scan_to_file(scanner, mode, resolution, filename):	
	scanProgram = 'scanimage --format=pnm'
	modeFlag = ' '.join(['--mode', mode])
	resolutionFlag = ' '.join(['--resolution', resolution])
	scannerFlag = ' '.join(['-d', scanner])
	outputFile = '>%s' % filename
	scanCmd = ' '.join([scanProgram, modeFlag, resolutionFlag, scannerFlag, outputFile])
	
	print 'Scanning with command: "%s"' % scanCmd
	output = commands.getoutput(scanCmd)
	
	if not os.path.exists(filename):
		print 'Scan failed: file %s not created.' % filename
		return SCAN_FAILURE
			
	print 'Scan complete'
	return SCAN_SUCCESS