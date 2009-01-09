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
This module contains the Python exceptions which take the place
of SANE's status codes in the Pythonic reimplementation of the API.
These are the errors that users will need to handle.
"""

# TODO: add detail parameters, e.g.: SaneUnsupportedOperationError should include the device as an attribute

class SaneError(Exception):
    """
    Base class for all SANE Errors.
    """
    pass
    
class SaneUnknownError(SaneError):
    """
    Exception denoting an error within the SANE library that could
    not be categorized.
    """
    pass
    
class SaneUnsupportedOperationError(SaneError):
    """
    Exception denoting an unsupported operation was requested.
    
    Corresponds to SANE status code SANE_STATUS_UNSUPPORTED.
    """
    pass
    
class SaneCancelledOperationError(SaneError):
    """
    TODO: when is this called
    
    Corresponds to SANE status code SANE_STATUS_CANCELLED.
    """
    pass
    
class SaneDeviceBusyError(SaneError):
    """
    Exception denoting that the requested device is being
    accessed by another process.
    
    Corresponds to SANE status code SANE_STATUS_DEVICE_BUSY.
    """
    pass
    
class SaneInvalidDataError(SaneError):
    """
    Exception denoting that some data or argument was not
    valid.
    
    Corresponds to SANE status code SANE_STATUS_INVAL.
    """
    pass
    
class SaneEndOfFileError(SaneError):
    """
    TODO: Should the user ever see this?  probably handled internally
    
    Corresponds to SANE status code SANE_STATUS_EOF.
    """
    pass
    
class SaneDeviceJammedError(SaneError):
    """
    Exception denoting that the device is jammed.
    
    Corresponds to SANE status code SANE_STATUS_JAMMED.
    """
    pass
    
class SaneNoDocumentsError(SaneError):
    """
    Exception denoting that there are pages in the document
    feeder of the device.
    
    Corresponds to SANE status code SANE_STATUS_NO_DOCS.
    """
    pass
    
class SaneCoverOpenError(SaneError):
    """
    Exception denoting that the cover of the device is open.
    
    Corresponds to SANE status code SANE_STATUS_COVER_OPEN.
    """
    pass
    
class SaneIOError(SaneError):
    """
    Exception denoting that an IO error occurred while
    communicating wtih the device.
    
    Corresponds to the SANE status code SANE_STATUS_IO_ERROR.
    """
    pass
    
class SaneOutOfMemoryError(SaneError):
    """
    Exception denoting that SANE ran out of memory during an
    operation.
    
    Corresponds to the SANE status code SANE_STATUS_NO_MEM.
    """
    pass
    
class SaneAccessDeniedError(SaneError):
    """
    TODO: should this be handled in a special way?
    
    Corresponds to the SANE status code SANE_STATUS_ACCESS_DENIED.
    """
    pass	