import os
from subprocess import Popen, PIPE, STDOUT
import threading
import signal
import re

SCAN_CANCELLED = -1
SCAN_FAILURE = 0
SCAN_SUCCESS = 1

def get_available_scanners():
	updateCmd = 'scanimage -f "%d=%v %m;"'
	updatePipe = Popen(updateCmd, shell=True, stderr=STDOUT, stdout=PIPE)
	updatePipe.wait()
	
	output = updatePipe.stdout.read()

	scannerDict = {}
	scannerList = re.findall('(.*)=(.*);', output)
	
	for v, k in scannerList:
		scannerDict[k] = v
		
	return scannerDict
	
def get_scanner_options(scanner):
	updateCmd = ' '.join(['scanimage --help -d',  scanner])
	updatePipe = Popen(updateCmd, shell=True, stderr=STDOUT, stdout=PIPE)
	updatePipe.wait()
	
	output = updatePipe.stdout.read()		
	
	modeList = re.findall('--mode (.*) ', output)[0].split('|')
	resolutionList = re.findall('--resolution (.*)dpi ', output)[0].split('|')
	
	return (modeList, resolutionList)

def scan_to_file(scanner, mode, resolution, filename, stopEvent):	
	scanProgram = 'scanimage --format=pnm'
	modeFlag = ' '.join(['--mode', mode])
	resolutionFlag = ' '.join(['--resolution', resolution])
	scannerFlag = ' '.join(['-d', scanner])
	outputFile = '>%s' % filename
	scanCmd = ' '.join([scanProgram, modeFlag, resolutionFlag, scannerFlag, outputFile])
	
	print 'Scanning with command: "%s"' % scanCmd
	scanPipe = Popen(scanCmd, shell=True, stderr=STDOUT, stdout=PIPE)
	
	while scanPipe.poll() == None:
		if stopEvent.isSet():
			os.kill(scanPipe.pid, signal.SIGTERM)
			print 'Scan terminated'
			return SCAN_CANCELLED
	
	if not os.path.exists(filename):
		print 'Scan failed: file %s not created.' % filename
		return SCAN_FAILURE
			
	print 'Scan complete'
	return SCAN_SUCCESS