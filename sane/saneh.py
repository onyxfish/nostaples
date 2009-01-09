#!/bin/python

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
This module contains the apples to apples conversion of the sane.h
header file to a Python/ctypes API.  Pains have been taken to
reproduce all typedefs, definitions, enumerations, structures, and
function prototypes as faithfully as possible.  Ctypes argtypes and
restype attributes have been used to apply type checking to the
function declarations.
"""

from ctypes import *
from ctypes.util import find_library

# LOAD LIBRARY

sane_path = find_library('sane')
libsane = cdll.LoadLibrary(sane_path)

# DEFINITIONS

#define SANE_VERSION_MAJOR(code)	((((SANE_Word)(code)) >> 24) &   0xff)
def SANE_VERSION_MAJOR(code):
    return (code.value >> 24) & 0xff
    
#define SANE_VERSION_MINOR(code)	((((SANE_Word)(code)) >> 16) &   0xff)
def SANE_VERSION_MINOR(code):
    return (code.value >> 16) & 0xff

#define SANE_VERSION_BUILD(code)	((((SANE_Word)(code)) >>  0) & 0xffff)
def SANE_VERSION_BUILD(code):
    return (code.value >> 0) & 0xffff
    
#define SANE_FIXED_SCALE_SHIFT	16
SANE_FIXED_SCALE_SHIFT = 16

#define SANE_FIX(v)	((SANE_Word) ((v) * (1 << SANE_FIXED_SCALE_SHIFT)))
def SANE_FIX(v):
    return v * (1 << SANE_FIXED_SCALE_SHIFT)

#define SANE_UNFIX(v)	((double)(v) / (1 << SANE_FIXED_SCALE_SHIFT))
def SANE_UNFIX(v):
    return v / (1 << SANE_FIXED_SCALE_SHIFT)
    
#define SANE_CAP_SOFT_SELECT		(1 << 0)
SANE_CAP_SOFT_SELECT = 1 << 0

#define SANE_CAP_HARD_SELECT		(1 << 1)
SANE_CAP_HARD_SELECT = 1 << 1

#define SANE_CAP_SOFT_DETECT		(1 << 2)
SANE_CAP_SOFT_DETECT = 1 << 2

#define SANE_CAP_EMULATED		(1 << 3)
SANE_CAP_EMULATED = 1 << 3

#define SANE_CAP_AUTOMATIC		(1 << 4)
SANE_CAP_AUTOMATIC = 1 << 4

#define SANE_CAP_INACTIVE		(1 << 5)
SANE_CAP_INACTIVE = 1 << 5

#define SANE_CAP_ADVANCED		(1 << 6)
SANE_CAP_ADVANCED = 1 << 6

#define SANE_CAP_ALWAYS_SETTABLE	(1 << 7)
SANE_CAP_ALWAYS_SETTABLE = 1 << 7

#define SANE_OPTION_IS_ACTIVE(cap)	(((cap) & SANE_CAP_INACTIVE) == 0)
def SANE_OPTION_IS_ACTIVE(cap):
    return ((cap & SANE_CAP_INACTIVE) == 0)

#define SANE_OPTION_IS_SETTABLE(cap)	(((cap) & SANE_CAP_SOFT_SELECT) != 0)
def SANE_OPTION_IS_SETTABLE(cap):
    return ((cap & SANE_CAP_SOFT_SELECT) != 0)

#define SANE_INFO_INEXACT		(1 << 0)
SANE_INFO_INEXACT = 1 << 0

#define SANE_INFO_RELOAD_OPTIONS	(1 << 1)
SANE_INFO_RELOAD_OPTIONS = 1 << 1

#define SANE_INFO_RELOAD_PARAMS		(1 << 2)
SANE_INFO_RELOAD_PARAMS = 1 << 2

#define SANE_MAX_USERNAME_LEN	128
SANE_MAX_USERNAME_LEN = 128

#define SANE_MAX_PASSWORD_LEN	128
SANE_MAX_PASSWORD_LEN = 128

# TYPEDEFS

SANE_Byte = c_ubyte
SANE_Word = c_int
SANE_Bool = SANE_Word
SANE_Int = SANE_Word
SANE_Char = c_char
SANE_String = c_char_p
SANE_String_Const = c_char_p
SANE_Handle = c_void_p
SANE_Fixed = SANE_Word

# ENUMERATIONS

# SANE_Status
SANE_Status = c_int

(SANE_STATUS_GOOD,
    SANE_STATUS_UNSUPPORTED,
    SANE_STATUS_CANCELLED,
    SANE_STATUS_DEVICE_BUSY,
    SANE_STATUS_INVAL,
    SANE_STATUS_EOF,
    SANE_STATUS_JAMMED,
    SANE_STATUS_NO_DOCS,
    SANE_STATUS_COVER_OPEN,
    SANE_STATUS_IO_ERROR,
    SANE_STATUS_NO_MEM,
    SANE_STATUS_ACCESS_DENIED) = map(c_int, xrange(12))

# SANE_Value_Type
SANE_Value_Type = c_int

(SANE_TYPE_BOOL,
    SANE_TYPE_INT,
    SANE_TYPE_FIXED,
    SANE_TYPE_STRING,
    SANE_TYPE_BUTTON,
    SANE_TYPE_GROUP) = map(c_int, xrange(6))

# SANE_Unit
SANE_Unit = c_int

(SANE_UNIT_NONE,
    SANE_UNIT_PIXEL,
    SANE_UNIT_BIT,
    SANE_UNIT_MM,
    SANE_UNIT_DPI,
    SANE_UNIT_PERCENT,
    SANE_UNIT_MICROSECOND) = map(c_int, xrange(7))
    
# SANE_Constraint_Type
SANE_Constraint_Type = c_int

(SANE_CONSTRAINT_NONE,
    SANE_CONSTRAINT_RANGE,
    SANE_CONSTRAINT_WORD_LIST,
    SANE_CONSTRAINT_STRING_LIST) = map(c_int, xrange(4))

# SANE_Action
SANE_Action = c_int

(SANE_ACTION_GET_VALUE ,
    SANE_ACTION_SET_VALUE,
    SANE_ACTION_SET_AUTO) = map(c_int, xrange(3))

# SANE_Frame
SANE_Frame = c_int

(SANE_FRAME_GRAY,
    SANE_FRAME_RGB,
    SANE_FRAME_RED,
    SANE_FRAME_GREEN,
    SANE_FRAME_BLUE) = map(c_int, xrange(5))

(SANE_FRAME_TEXT,
    SANE_FRAME_JPEG,
    SANE_FRAME_G31D,
    SANE_FRAME_G32D,
    SANE_FRAME_G42D,
    SANE_FRAME_IR,
    SANE_FRAME_RGBI,
    SANE_FRAME_GRAYI) = map(c_int, xrange(10, 18))

# STRUCTURES & UNIONS

class SANE_Range(Structure):
    _fields_ = [
        ("min", SANE_Word),
        ("max", SANE_Word),
        ("quant", SANE_Word)]

class SANE_Constraint(Union):
    _fields_ = [
        ("string_list", POINTER(SANE_String_Const)),
        ("word_list", POINTER(SANE_Word)),
        ("range", POINTER(SANE_Range))]
        
class SANE_Option_Descriptor(Structure):
    _fields_ = [
        ("name",  SANE_String_Const),
        ("title", SANE_String_Const),
        ("desc", SANE_String_Const),
        ("type", SANE_Value_Type),
        ("unit", SANE_Unit),
        ("size", SANE_Int),
        ("cap", SANE_Int),
        ("constraint_type", SANE_Constraint_Type),
        ("constraint", SANE_Constraint)]
        
class SANE_Device(Structure):
    _fields_ = [
        ("name", SANE_String_Const),
        ("vendor", SANE_String_Const),
        ("model", SANE_String_Const),
        ("type", SANE_String_Const)]
        
class SANE_Parameters(Structure):
    _fields_ = [
        ("format", SANE_Frame),
        ("last_frame", SANE_Bool),
        ("bytes_per_line", SANE_Int),
        ("pixels_per_line", SANE_Int),
        ("lines", SANE_Int),
        ("depth", SANE_Int)]

# CALLBACKS

#typedef void (*SANE_Auth_Callback) (SANE_String_Const resource, SANE_Char *username, SANE_Char *password);
SANE_Auth_Callback = CFUNCTYPE(SANE_String_Const, POINTER(SANE_Char), POINTER(SANE_Char))

# FUNCTION PROTOTYPES

#extern SANE_Status sane_init (SANE_Int * version_code, SANE_Auth_Callback authorize);
sane_init = libsane.sane_init
sane_init.argtypes = [POINTER(SANE_Int), SANE_Auth_Callback]
sane_init.restype = SANE_Status

#extern void sane_exit (void);
sane_exit = libsane.sane_exit

#extern SANE_Status sane_get_devices (const SANE_Device *** device_list, SANE_Bool local_only);
sane_get_devices = libsane.sane_get_devices
sane_get_devices.argtypes = [POINTER(POINTER(POINTER(SANE_Device))), SANE_Bool]
sane_get_devices.restype = SANE_Status

#extern SANE_Status sane_open (SANE_String_Const devicename, SANE_Handle * handle);
sane_open = libsane.sane_open
sane_open.argtypes = [SANE_String_Const, POINTER(SANE_Handle)]
sane_open.restype = SANE_Status

#extern void sane_close (SANE_Handle handle);
sane_close = libsane.sane_close
sane_close.argtypes = [SANE_Handle]

#extern const SANE_Option_Descriptor * sane_get_option_descriptor (SANE_Handle handle, SANE_Int option);
sane_get_option_descriptor = libsane.sane_get_option_descriptor
sane_get_option_descriptor.argtypes = [SANE_Handle, SANE_Int]
sane_get_option_descriptor.restype = POINTER(SANE_Option_Descriptor)

#extern SANE_Status sane_control_option (SANE_Handle handle, SANE_Int option, SANE_Action action, void *value, SANE_Int * info);
sane_control_option = libsane.sane_control_option
sane_control_option.argtypes = [SANE_Handle, SANE_Int, SANE_Action, c_void_p, POINTER(SANE_Int)]
sane_control_restype = SANE_Status

#extern SANE_Status sane_get_parameters (SANE_Handle handle, SANE_Parameters * params);
sane_get_parameters = libsane.sane_get_parameters
sane_get_parameters.argtypes = [SANE_Handle, POINTER(SANE_Parameters)]
sane_get_parameters.restype = SANE_Status
                    
#extern SANE_Status sane_start (SANE_Handle handle);
sane_start = libsane.sane_start
sane_start.argtypes = [SANE_Handle]
sane_start.restype = SANE_Status

#extern SANE_Status sane_read (SANE_Handle handle, SANE_Byte * data, SANE_Int max_length, SANE_Int * length);
sane_read = libsane.sane_read
sane_read.argtypes = [SANE_Handle, POINTER(SANE_Byte), SANE_Int, POINTER(SANE_Int)]
sane_read.restype = SANE_Status
                  
#extern void sane_cancel (SANE_Handle handle);
sane_cancel = libsane.sane_cancel
sane_cancel.argtypes = [SANE_Handle]

#extern SANE_Status sane_set_io_mode (SANE_Handle handle, SANE_Bool non_blocking);
sane_set_io_mode = libsane.sane_set_io_mode
sane_set_io_mode.argtypes = [SANE_Handle, SANE_Bool]
sane_set_io_mode.restype = SANE_Status
                     
#extern SANE_Status sane_get_select_fd (SANE_Handle handle, SANE_Int * fd);
sane_get_select_fd = libsane.sane_get_select_fd
sane_get_select_fd.argtypes = [SANE_Handle, POINTER(SANE_Int)]
sane_get_select_fd.restype = SANE_Status
                       
#extern SANE_String_Const sane_strstatus (SANE_Status status);
sane_strstatus = libsane.sane_strstatus
sane_strstatus.argtypes = [SANE_Status]
sane_strstatus.restype = SANE_String_Const

# HELPER FUNCTIONS (TEMP)
        
def sane_status_to_string(status):
    sane_strstatus = libsane.sane_strstatus
    sane_strstatus.restype = SANE_String_Const
    return sane_strstatus(status)
    
def sane_auth_callback(resource, username, password):
    print resource, username, password

if __name__ == "__main__":
    version_code = SANE_Int(0)
    callback = SANE_Auth_Callback(sane_auth_callback)
    status = sane_init(byref(version_code), callback)

    print sane_status_to_string(status)
    print SANE_VERSION_MAJOR(version_code), SANE_VERSION_MINOR(version_code), SANE_VERSION_BUILD(version_code)
    
    #it stores a pointer to a NULL terminated array of pointers to SANE_Device structures in *device_list. 

    devices = POINTER(POINTER(SANE_Device))()

    status = sane_get_devices(byref(devices), SANE_Bool(0))

    num_devices = 0
    # Convert NULL-terminated C list into Python list
    device_list = []
    while devices[num_devices]:
        device_list.append(devices[num_devices].contents)  # use .contents here since each entry in the C list is itself a pointer
        num_devices += 1
        
    print device_list, len(device_list), device_list[0].name
    
    handle = SANE_Handle()
    
    status = sane_open(device_list[0].name, byref(handle))
    
    print sane_status_to_string(status), handle
    
    status = sane_start(handle)
    
    print sane_status_to_string(status)
    
    
    
    sane_close(handle)
    
    sane_exit()