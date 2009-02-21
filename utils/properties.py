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
This module holds the utilities that ease the burden of working with
python-gtkmvc properties.
"""
    
class GenericPropertySetter(object):
    """
    This callable object overrides the python-gtkmvc
    accessors established in gtkmvc.support.metaclass_base.py.
    
    It handles not only notifying observers of changes in the 
    property, but also persist changes to the state backend.
    """
    def __init__(self, property_name):
        """
        Store the property name which is visible to the
        application as well as its attribute name.
        """
        self.property_name = property_name
        self.property_attr_name = '_prop_%s' % self.property_name
    
    def __call__(self, cls, value):
        """
        Write state and notify observers of changes.
        
        For more details on how this works see
        L{set_prop_active_scanner}.
        """
        old_value = getattr(cls, self.property_attr_name)
        if old_value == value:
            return
        setattr(cls, self.property_attr_name, value)
        cls.application.get_state_manager()[self.property_name] = value
        cls.notify_property_value_change(
            self.property_name, old_value, value)
        
class GenericStateCallback(object):
    """
    This callable object encasuplates the most common reaction to
    a state callback: setting the attribute on the model
    (which in turn causes property notifications, etc).
    """
    def __init__(self, model, property_name):
        """
        Store property a name as well as the model
        that owns this property.
        """
        self.model = model
        self.property_name = property_name
        
    def __call__(self):
        """
        Set the property attribute on the model, initiating
        observer callbacks, etc.
        """
        setattr(
            self.model, 
            self.property_name, 
            self.model.application.get_state_manager()[self.property_name])