#!/usr/bin/python

#~ This file is part of SaneMe.

#~ SaneMe is free software: you can redistribute it and/or modify
#~ it under the terms of the GNU General Public License as published by
#~ the Free Software Foundation, either version 3 of the License, or
#~ (at your option) any later version.

#~ SaneMe is distributed in the hope that it will be useful,
#~ but WITHOUT ANY WARRANTY; without even the implied warranty of
#~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#~ GNU General Public License for more details.

#~ You should have received a copy of the GNU General Public License
#~ along with SaneMe.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains the Pythonic implementation of the SANE API.
The flat C functions have been wrapped in a set of objects and all
ctypes of the underlying implmentation have been hidden from the
user's view.  This enumerations and definiations which are absolutely
necessary to the end user have been redeclared.
"""

# TODO: document what exceptions can be thrown by each method

from array import *
import atexit
import ctypes
from types import *

from PIL import Image

from errors import *
from saneh import *

# Redeclare saneh enumerations which are visible to the application
(OPTION_TYPE_BOOL,
    OPTION_TYPE_INT,
    OPTION_TYPE_FIXED,
    OPTION_TYPE_STRING,
    OPTION_TYPE_BUTTON,
    OPTION_TYPE_GROUP) = xrange(6)
    
(OPTION_UNIT_NONE,
    OPTION_UNIT_PIXEL,
    OPTION_UNIT_BIT,
    OPTION_UNIT_MM,
    OPTION_UNIT_DPI,
    OPTION_UNIT_PERCENT,
    OPTION_UNIT_MICROSECOND) = xrange(7)
    
(OPTION_CONSTRAINT_NONE,
    OPTION_CONSTRAINT_RANGE,
    OPTION_CONSTRAINT_INTEGER_LIST,
    OPTION_CONSTRAINT_STRING_LIST) = xrange(4)

class SaneMe(object):
    """
    The top-level object for interacting with the SANE API.  Handles
    polling for devices.  This object should only be instantiated once.
    """
    _log = None
    
    _version = None  # (major, minor, build)
    _devices = []
    
    def __init__(self, log=None):
        """
        Create the SANE object, perform setup, and register
        the cleanup function.
        
        @param log: an optional Python logging object to log to.
        """
        self._log = log
        
        self._setup()
        atexit.register(self._shutdown)
        
    # Read only properties

    def __get_version(self):
        """Get the current installed version of SANE."""
        return self._version
        
    version = property(__get_version)
    
    def _setup(self):
        """
        Iniitalize SANE and retrieve the current installed version.
        """
        version_code = SANE_Int()
        auth_callback = SANE_Auth_Callback(self._sane_auth_callback)
        
        status = sane_init(byref(version_code), auth_callback) 
        
        if status != SANE_STATUS_GOOD.value:
            raise SaneUnknownError(
                'sane_init returned an invalid status.')
        
        self._version = (SANE_VERSION_MAJOR(version_code), 
            SANE_VERSION_MINOR(version_code), 
            SANE_VERSION_BUILD(version_code))
        
        if self._log:
            self._log.debug('SANE version %s initalized.', self._version)
            
    def _sane_auth_callback(self, resource, username, password):
        """
        TODO
        """
        raise NotImplementedError(
            'sane_auth_callback requested, but not yet implemented.')
        
    def _shutdown(self):
        """
        Deinitialize SANE.
        
        This code would go in L{__del__}, but it is not guaranteed that method
        will be called and sane_exit must be called to release resources.  To
        ensure this method is called it is registered with atexit.
        """
        for device in self._devices:
            if device.is_open():
                device.close()
                
        sane_exit()
        self._version = None
        
        if self._log:
            self._log.debug('SANE deinitialized.')
        
    # Public Methods
    
    def get_device_list(self):
        """
        Poll for connected devices.  This method may take several
        seconds to return.
        
        Note that SANE is exited and re-inited before querying for
        devices to workaround a limitation in SANE's USB driver
        which causes the device list to only be updated on init.
        
        This means that all settings applied to all devices will be
        B{lost} and must be restored by the calling application.
        
        This was found documented here:        
        U{http://www.nabble.com/sane_get_devices-and-sanei_usb_init-td20766234.html}
        """
        assert self._version is not None
        
        # See docstring for details on this voodoo
        self._shutdown()
        self._setup()
        
        cdevices = POINTER(POINTER(SANE_Device))()
        status = sane_get_devices(byref(cdevices), SANE_Bool(0))
        
        if status == SANE_STATUS_GOOD.value:
            pass
        elif status == SANE_STATUS_NO_MEM.value:
            raise SaneOutOfMemoryError(
                'sane_get_devices ran out of memory.')
        else:
            raise SaneUnknownError(
                'sane_get_devices returned an invalid status.')

        device_count = 0
        self._devices = []
        
        while cdevices[device_count]:
            self._devices.append(Device(cdevices[device_count].contents))
            device_count += 1
           
        if self._log:
            self._log.debug('SANE queried, %i device(s) found.', device_count)
            
        return self._devices
        
    def get_device_by_name(self, name):
        """
        Retrieve a L{Device} by name.
        
        Must be preceded by a call to L{get_device_list}.
        """
        for device in self._devices:
            if device.name == name:
                return device
            
        raise SaneNoSuchDeviceError()
        
class Device(object):
    """
    This is the primary object for interacting with SANE.  It represents
    a single device and handles enumeration of options, getting and
    setting of options, and starting and stopping of scanning jobs.
    """   
    _log = None
    
    _handle = None
    
    _name = ''
    _vendor = ''
    _model = ''
    _type = ''
    
    _display_name = ''
    
    _options = {}
    
    def __init__(self, ctypes_device, log=None):
        """
        Sets the Devices properties from a ctypes SANE_Device and
        queries for its available options.
        """
        self._log = log
        
        assert type(ctypes_device.name) is StringType
        assert type(ctypes_device.vendor) is StringType
        assert type(ctypes_device.model) is StringType
        assert type(ctypes_device.type) is StringType
        
        self._name = ctypes_device.name
        self._vendor = ctypes_device.vendor
        self._model = ctypes_device.model
        self._type = ctypes_device.type
        
        self._display_name = ' '.join([self._vendor, self._model])
        
    # Read only properties

    def __get_name(self):
        """
        Get the complete SANE identifier for this device, 
        e.g. 'lexmark:libusb:002:006'.
        """
        return self._name
        
    name = property(__get_name)
    
    def __get_vendor(self):
        """Get the manufacturer of this device, e.g. 'Lexmark'."""
        return self._vendor
        
    vendor = property(__get_vendor)
    
    def __get_model(self):
        """Get the specific model of this device, e.g. 'X1100/rev. B2'."""
        return self._model
        
    model = property(__get_model)
    
    def __get_type(self):
        """Get the type of this device, e.g. 'flatbed scanner'."""
        return self._type
        
    type = property(__get_type)
    
    def __get_display_name(self):
        """
        Get an appropriate name to use for displaying this device
        to a user, e.g. 'Lexmark X1100/rev. B2'."""
        return self._display_name
        
    display_name = property(__get_display_name)
    
    def __get_options(self):
        """Get the dictionary of options that this device has."""
        return self._options
        
    options = property(__get_options)
    
    # Internal methods
        
    def _update_options(self):
        """
        Update the list of available options for this device.  As these
        are immutable, this should only need to be called when the Device
        is first instantiated.
        """
        assert self._handle is not None
        assert self._handle != c_void_p(None)
        
        option_value = pointer(c_int())
        status = sane_control_option(self._handle, 0, SANE_ACTION_GET_VALUE, option_value, None)
        
        if status == SANE_STATUS_GOOD.value:
            pass
        elif status == SANE_STATUS_UNSUPPORTED.value:
            raise SaneUnsupportedOperationError(
                'sane_control_option reported that a value was outside the option\'s constraint.')
        elif status == SANE_STATUS_INVAL.value:
            raise AssertionError(
                'sane_open reported that the device name was invalid.')
        elif status == SANE_STATUS_IO_ERROR.value:
            raise SaneIOError(
                'sane_open reported a communications error.')
        elif status == SANE_STATUS_NO_MEM.value:
            raise SaneOutOfMemoryError(
                'sane_open ran out of memory.')
        elif status == SANE_STATUS_ACCESS_DENIED.value:
            raise SaneAccessDeniedError(
                'sane_open requires greater access to open the device.')
        else:
            raise SaneUnknownError(
                'sane_open returned an invalid status.')
        
        option_count = option_value.contents.value
        
        if self._log:
            self._log.debug('Device queried, %i option(s) found.', option_count)
        
        self._options.clear()
        
        i = 1
        while(i < option_count - 1):
            coption = sane_get_option_descriptor(self._handle, i)
            self._options[coption.contents.name] = Option(self, i, coption.contents)
            i = i + 1
        
    # Methods for use only by Options
    
    def _get_handle(self):
        """
        Verify that the device is open and get the current open handle.
        
        To be called by Options of this device so that they may set themselves.
        """
        assert self._handle is not None
        assert self._handle != c_void_p(None)
        
        return self._handle
        
    # Public methods
        
    def open(self):
        """
        Open a new handle to this device.
        
        Must be called before any operations (including setting options)
        are performed on this device.
        """
        assert self._handle is None
        self._handle = SANE_Handle()
        
        status = sane_open(self.name, byref(self._handle))
        
        if status == SANE_STATUS_GOOD.value:
            pass
        elif status == SANE_STATUS_DEVICE_BUSY.value:
            raise SaneDeviceBusyError(
                'sane_open reported that the device was busy.')
        elif status == SANE_STATUS_INVAL.value:
            # TODO - invalid device name?  disconnected?
            raise AssertionError(
                'sane_open reported that the device name was invalid.')
        elif status == SANE_STATUS_IO_ERROR.value:
            raise SaneIOError(
                'sane_open reported a communications error.')
        elif status == SANE_STATUS_NO_MEM.value:
            raise SaneOutOfMemoryError(
                'sane_open ran out of memory.')
        elif status == SANE_STATUS_ACCESS_DENIED.value:
            raise SaneAccessDeniedError(
                'sane_open requires greater access to open the device.')
        else:
            raise SaneUnknownError(
                'sane_open returned an invalid status.')
        
        assert self._handle != c_void_p(None)
        
        if self._log:
            self._log.debug('Device %s open.', self._name)
            
        self._update_options()
        
    def is_open(self):
        """
        Return true if there is an active handle to this device.
        """
        return (self._handle is not None)

    def close(self):
        """
        Close the current handle to this device.  All changes made
        to its options will be lost.
        """
        assert self._handle is not None
        assert self._handle != c_void_p(None)
        
        sane_close(self._handle)        
        self._handle = None
        
        if self._log:
            self._log.debug('Device %s closed.', self._name)
            
    def scan(self, progress_callback=None):
        """
        Scan a document using this device.
        
        TODO: handle ADF scans
        
        @param progress_callback: An optional callback that
            will be called each time data is read from
            the device.  Has the format:
            cancel = progress_callback(sane_info, bytes_read)
        @return: A PIL image containing the scanned
            page.
        """
        assert self._handle is not None
        assert self._handle != c_void_p(None)
        
        # See SANE API 4.3.9
        status = sane_start(self._handle)
        
        if status == SANE_STATUS_GOOD.value:
            pass
        elif status == SANE_STATUS_CANCELLED.value:
            raise AssertionError(
                'sane_start reported cancelled status before it was set.')
        elif status == SANE_STATUS_DEVICE_BUSY.value:
            raise SaneDeviceBusyError(
                'sane_start reported the device was in use.')
        elif status == SANE_STATUS_JAMMED.value:
            raise SaneDeviceJammedError(
                'sane_start reported a paper jam.')
        elif status == SANE_STATUS_NO_DOCS.value:
            raise SaneNoDocumentsError(
                'sane_start reported that the document feeder was empty.')
        elif status == SANE_STATUS_COVER_OPEN.value:
            raise SaneCoverOpenError(
                'sane_start reported that the device cover was open.')
        elif status == SANE_STATUS_IO_ERROR.value:
            raise SaneIOError(
                'sane_start encountered a communications error.')
        elif status == SANE_STATUS_NO_MEM.value:
            raise SaneOutOfMemoryError(
                'sane_start ran out of memory.')
        elif status == SANE_STATUS_INVAL.value:
            #TODO - see docs
            raise SaneInvalidDataError()
        else:
            raise SaneUnknownError(
                'sane_start returned an invalid status.')
        
        sane_parameters = SANE_Parameters()
        
        # See SANE API 4.3.8
        status = sane_get_parameters(self._handle, byref(sane_parameters))
        
        if status != SANE_STATUS_GOOD.value:
            raise SaneUnknownError()

        scan_info = ScanInfo(sane_parameters)
        
        # This is the size used for the scan buffer in SANE's scanimage
        # utility.  The precise reasoning for using 32kb is unclear.
        bytes_per_read = 32768
        
        data_array = array('B')
        temp_array = (SANE_Byte * bytes_per_read)()
        actual_size = SANE_Int()
        
        cancel = False
        
        while True:
            # See SANE API 4.3.10
            status = sane_read(self._handle, temp_array, bytes_per_read, byref(actual_size))
            
            if status == SANE_STATUS_GOOD.value:
                pass
            elif status == SANE_STATUS_EOF.value:
                break
            elif status == SANE_STATUS_CANCELLED.value:
                return None
            elif status == SANE_STATUS_JAMMED.value:
                raise SaneDeviceJammedError(
                    'sane_read reported a paper jam.')
            elif status == SANE_STATUS_NO_DOCS.value:
                raise SaneNoDocumentsError(
                    'sane_read reported that the document feeder was empty.')
            elif status == SANE_STATUS_COVER_OPEN.value:
                raise SaneCoverOpenError(
                    'sane_read reported that the device cover was open.')
            elif status == SANE_STATUS_IO_ERROR.value:
                raise SaneIOError(
                    'sane_read encountered a communications error.')
            elif status == SANE_STATUS_NO_MEM.value:
                raise SaneOutOfMemoryError(
                    'sane_read ran out of memory.')
            elif status == SANE_STATUS_ACCESS_DENIED.value:
                raise SaneAccessDeniedError(
                    'sane_read requires greater access to open the device.')
            else:
                raise SaneUnknownError(
                    'sane_read returned an invalid status.')
            
            data_array.extend(temp_array[0:actual_size.value])
            
            if progress_callback:
                cancel = progress_callback(scan_info, len(data_array))
                
                if cancel:
                    sane_cancel(self._handle)
                    return None

        assert not cancel
        
        sane_cancel(self._handle)
        
        assert scan_info.total_bytes == len(data_array)
        
        if sane_parameters.format == SANE_FRAME_GRAY.value:
            pil_image = Image.frombuffer(
                'L', (scan_info.width, scan_info.height), 
                data_array, 'raw', 'L', 0, 1)
        elif sane_parameters.format == SANE_FRAME_RGB.value:
            pil_image = Image.frombuffer(
                'RGB', (scan_info.width, scan_info.height), 
                data_array, 'raw', 'RGB', 0, 1)
        else:
            # TODO
            raise NotImplementedError(
               'Individual color frame scanned, but not yet supported.')
            
        return pil_image
    
class Option(object):
    """
    Represents a single option available for a device.  Exposes
    a variety of information designed to make it easy for a GUI
    to render each arbitrary option in a user-friendly way.
    """
    log = None
    
    _device = None
    _option_number = 0
    
    _name = ''
    _title = ''
    _description = ''
    _type = 0
    _unit = 0
    _size = 0
    _capabilities = 0
    _constraint_type = 0
    
    _constraint = None
    
    def __init__(self, device, option_number, ctypes_option, log=None): 
        """
        Construct the option from a given ctypes SANE_Option_Descriptor.
        Parse the necessary constraint information from the
        SANE_Constraint and SANE_Range structures.
        """
        self._log = log
        
        self._device = device
        self._option_number = option_number
        
        assert type(ctypes_option.name) is StringType
        assert type(ctypes_option.title) is StringType
        assert type(ctypes_option.desc) is StringType
        assert type(ctypes_option.type) is IntType
        assert type(ctypes_option.unit) is IntType
        assert type(ctypes_option.size) is IntType
        assert type(ctypes_option.cap) is IntType
        assert type(ctypes_option.constraint_type) is IntType
        
        self._name = ctypes_option.name
        self._title = ctypes_option.title
        self._description = ctypes_option.desc
        self._type = ctypes_option.type
        self._unit = ctypes_option.unit
        self._size = ctypes_option.size
        self._capability = ctypes_option.cap
        self._constraint_type = ctypes_option.constraint_type
        
        if self._constraint_type == SANE_CONSTRAINT_NONE.value:
            pass
        elif self._constraint_type == SANE_CONSTRAINT_RANGE.value:
            assert type(ctypes_option.constraint.range) is POINTER(SANE_Range)
            assert type(ctypes_option.constraint.range.contents.min) is IntType
            assert type(ctypes_option.constraint.range.contents.max) is IntType
            assert type(ctypes_option.constraint.range.contents.quant) is IntType
            
            self._constraint = (
                ctypes_option.constraint.range.contents.min,
                ctypes_option.constraint.range.contents.max,
                ctypes_option.constraint.range.contents.quant)
        elif self._constraint_type == SANE_CONSTRAINT_WORD_LIST.value:
            assert type(ctypes_option.constraint.word_list) is POINTER(SANE_Word)
            
            word_count = ctypes_option.constraint.word_list[0]
            self._constraint = []
            
            i = 1
            while(i < word_count):
                self._constraint.append(ctypes_option.constraint.word_list[i])
                i = i + 1                
        elif self._constraint_type == SANE_CONSTRAINT_STRING_LIST.value:
            assert type(ctypes_option.constraint.string_list) is POINTER(SANE_String_Const)

            string_count = 0
            self._constraint = []
            
            while ctypes_option.constraint.string_list[string_count]:
                self._constraint.append(ctypes_option.constraint.string_list[string_count])
                string_count += 1
        
    # Read only properties

    def __get_name(self):
        """Get the short-form name of this option, e.g. 'mode'."""
        return self._name
        
    name = property(__get_name)

    def __get_title(self):
        """Get the full name of this option, e.g. 'Scan mode'."""
        return self._title
        
    title = property(__get_title)

    def __get_description(self):
        """
        Get the full description of this option,
        e.g. 'Selects the scan mode (e.g., lineart, monochrome, or color).'
        """
        return self._description
        
    description = property(__get_description)

    def __get_type(self):
        return self._type
        
    type = property(__get_type)

    def __get_unit(self):
        return self._unit
        
    unit = property(__get_unit)

    def __get_capability(self):
        # TODO: break out into individual capabilities, rather than a bitset
        return self._capability
        
    capability = property(__get_capability)

    def __get_constraint_type(self):
        return self._constraint_type
        
    constraint_type = property(__get_constraint_type)

    def __get_constraint(self):
        """
        Get the constraint for this option.
        
        If constraint_type is OPTION_CONSTRAINT_RANGE then
        this is a tuple containing the (minimum, maximum, step)
        for valid values.
        
        If constraint_type is OPTION_CONSTRAINT_INTEGER_LIST then
        this is a list of integers which are valid values.
        
        If constraint_type is OPTION_CONSTRAINT_STRING_LIST then
        this is a list of strings which are valid values.
        """
        return self._constraint
        
    constraint = property(__get_constraint)
        
    def __get_value(self):
        """
        Get the current value of this option.
        """
        handle = self._device._get_handle()
        
        if self._type == SANE_TYPE_BOOL.value:
            option_value = pointer(SANE_Bool())
        elif self._type == SANE_TYPE_INT.value:
            # TODO: these may not always be a single char wide, see SANE doc 4.2.9.6
            option_value = pointer(SANE_Int())
        elif self._type == SANE_TYPE_FIXED.value:
            # TODO: these may not always be a single char wide, see SANE doc 4.2.9.6
            option_value = pointer(SANE_Fixed())
        elif self._type == SANE_TYPE_STRING.value:
            # sane_control_option expects a mutable string buffer
            option_value = create_string_buffer(self._size)
        elif self._type == SANE_TYPE_BUTTON.value:
            raise TypeError('SANE_TYPE_BUTTON has no value.')
        elif self._type == SANE_TYPE_GROUP.value:
            raise TypeError('SANE_TYPE_GROUP has no value.')
        else:
            raise TypeError('Option is of unknown type.')
        
        status = sane_control_option(handle, self._option_number, SANE_ACTION_GET_VALUE, option_value, None)
        
        if status == SANE_STATUS_GOOD.value:
            pass
        elif status ==  SANE_STATUS_UNSUPPORTED.value:
            # Constraint checking ensures this should never happen
            raise AssertionError(
                'sane_control_option reported that a value was outside the option\'s constraint.')
        elif status == SANE_STATUS_INVAL.value:
            raise AssertionError(
                'sane_control_option reported a value was invalid, but no values was being set.')
        elif status == SANE_STATUS_IO_ERROR.value:
            raise SaneIOError(
                'sane_control_option reported a communications error.')
        elif status == SANE_STATUS_NO_MEM.value:
            raise SaneOutOfMemoryError(
                'sane_control_option ran out of memory.')
        elif status == SANE_STATUS_ACCESS_DENIED.value:
            raise SaneAccessDeniedError(
                'sane_control_option requires greater access to open the device.')
        else:
            raise SaneUnknownError(
                'sane_control_option returned an invalid status.')
        
        if self._type == SANE_TYPE_STRING.value:
            option_value = option_value.value
        else:
            option_value = option_value.contents.value
            
        if self._log:
            self._log.debug('Option %s queried, its current value is %s.', self._name, option_value)
            
        return option_value
    
    def __set_value(self, value):
        """
        Set the current value of this option.
        """
        handle = self._device._get_handle()
        
        c_value = None
        
        # Type checking
        if self._type == SANE_TYPE_BOOL.value:
            assert type(value) is BooleanType
            c_value = pointer(c_int(value))
        elif self._type == SANE_TYPE_INT.value:
            # TODO: these may not always be a single char wide, see SANE doc 4.2.9.6
            assert type(value) is IntType
            c_value = pointer(c_int(value))
        elif self._type == SANE_TYPE_FIXED.value:
            # TODO: these may not always be a single char wide, see SANE doc 4.2.9.6
            assert type(value) is IntType
            c_value = pointer(c_int(value))
        elif self._type == SANE_TYPE_STRING.value:
            assert type(value) is StringType
            assert len(value) + 1 < self._size
            c_value = c_char_p(value)
        elif self._type == SANE_TYPE_BUTTON.value:
            raise TypeError('SANE_TYPE_BUTTON has no value.')
        elif self._type == SANE_TYPE_GROUP.value:
            raise TypeError('SANE_TYPE_GROUP has no value.')
        else:
            raise TypeError('Option is of unknown type.')
        
        # Constraint checking
        if self._constraint_type == SANE_CONSTRAINT_NONE.value:
            pass
        elif self._constraint_type == SANE_CONSTRAINT_RANGE.value:
            assert value >= self._constraint[0]
            assert value <= self._constraint[1]
            assert value % self._constraint[2] == 0
        elif self._constraint_type == SANE_CONSTRAINT_WORD_LIST.value:
            assert value in self._constraint
        elif self._constraint_type == SANE_CONSTRAINT_STRING_LIST.value:
            assert value in self._constraint
            
        info_flags = SANE_Int()
        
        status = sane_control_option(
            handle, self._option_number, SANE_ACTION_SET_VALUE, c_value, byref(info_flags))
        
        if status == SANE_STATUS_GOOD.value:
            pass
        elif status ==  SANE_STATUS_UNSUPPORTED.value:
            # Constraint checking ensures this should never happen
            raise AssertionError(
                'sane_control_option reported that a value was outside the option\'s constraint.')
        elif status == SANE_STATUS_INVAL.value:
            raise AssertionError(
                'sane_control_option reported that the value to be set was invalid, despite checks.')
        elif status == SANE_STATUS_IO_ERROR.value:
            raise SaneIOError(
                'sane_control_option reported a communications error.')
        elif status == SANE_STATUS_NO_MEM.value:
            raise SaneOutOfMemoryError(
                'sane_control_option ran out of memory.')
        elif status == SANE_STATUS_ACCESS_DENIED.value:
            raise SaneAccessDeniedError(
                'sane_control_option requires greater access to open the device.')
        else:
            raise SaneUnknownError(
                'sane_control_option returned an invalid status.')
        
        if self._log:
            self._log.debug('Option %s set to value %s.', self._name, value)
        
        # See SANE API 4.3.7
        if info_flags.value & SANE_INFO_RELOAD_OPTIONS:
            raise SaneReloadOptionsError()
        
    value = property(__get_value, __set_value)
    
class ScanInfo(object):
    """
    Contains the parameters and progress of a scan in progress.
    """
    _width = 0
    _height = 0
    _depth = 0
    _total_bytes = 0
    
    def __init__(self, sane_parameters):
        """
        Initialize the ScanInfo object from the sane_parameters.
        """
        self._width = sane_parameters.pixels_per_line
        self._height = sane_parameters.lines
        self._depth = sane_parameters.depth
        self._total_bytes = sane_parameters.bytes_per_line * sane_parameters.lines
        
    # Read only properties

    def __get_width(self):
        """Get the width of the current scan, in pixels."""
        return self._width
        
    width = property(__get_width)

    def __get_height(self):
        """Get the height of the current scan, in pixels."""
        return self._height
        
    height = property(__get_height)

    def __get_depth(self):
        """Get the depth of the current scan, in bits."""
        return self._depth
        
    depth = property(__get_depth)

    def __get_total_bytes(self):
        """Get the total number of bytes comprising this scan."""
        return self._total_bytes
        
    total_bytes = property(__get_total_bytes)
        
if __name__ == '__main__':
    def progress_callback(sane_info, bytes_read):
        #print float(bytes_read) / sane_info.total_bytes
        pass
    
    import logging
    log_format = FORMAT = "%(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    
    sane = SaneMe(logging.getLogger())
    devices = sane.get_device_list()
    
    for dev in devices:
        print dev.name
        
    devices[0].open()
    
    print devices[0].options.keys()
    
    try:
        devices[0].options['mode'].value = 'Gray'
    except SaneReloadOptionsError:
        pass
    
    try:
        devices[0].options['resolution'].value = 75
    except SaneReloadOptionsError:
        pass
    
    try:
        devices[0].options['preview'].value = False
    except SaneReloadOptionsError:
        pass
    
    devices[0].scan(progress_callback).save('out.bmp')
    
    devices[0].close()