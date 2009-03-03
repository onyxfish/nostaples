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
Executing this module runs all the NoStaples unittests.  Pass -v
for detailed output.
"""

import sys

try:
    import nose
except ImportError:
    print 'You must have python-nose installed to run these tests.'
    sys.exit()
    
try:
    import mock
except ImportError:
    print 'You must have Michael Foord\'s Mock installed to run these tests.'
    sys.exit()
    
nose.run()