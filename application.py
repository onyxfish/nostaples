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
This module holds NoStaples' main method which handles
the instantiation of MVC objects and then starts the gtk
main loop.
"""

import logging.config
import os

import gtk

import constants
from controllers.about import AboutController
from controllers.document import DocumentController
from controllers.main import MainController
from controllers.page import PageController
from controllers.preferences import PreferencesController
from controllers.save import SaveController
from models.document import DocumentModel
from models.main import MainModel
from models.page import PageModel
from models.preferences import PreferencesModel
from models.save import SaveModel
from utils.state import GConfStateManager
from views.about import AboutView
from views.document import DocumentView
from views.main import MainView
from views.page import PageView
from views.preferences import PreferencesView
from views.save import SaveView

class Application(object):
    """
    A 'front controller' class that stores references to all
    top-level components of the application and facilitates
    communication between them.
    
    A reference to this class is injected into each controller
    component of the application via its constructor.  These 
    components then query the application object when they
    need to access other parts of the system.
    
    TODO: remove model/controller parameters from all component contstructuters.
    they are already getting a reference to application so they can just query
    for those other components
    """
    
    _state_manager = None
    
    _main_model = None
    _main_controller = None
    _main_view = None
    
    _preferences_model = None
    _preferences_controller = None
    _preferences_view = None
    
    _document_model = None
    _document_controller = None
    _document_view = None
    
    _null_page_model = None
    _page_controller = None
    _page_view = None
    
    _save_model = None
    _save_controller = None
    _save_view = None
    
    _about_controller = None
    _about_view = None

    def __init__(self):
        """
        Set up the config directory, logging, and state
        persistence.  Construct the Main MVC component triplet
        (which will in turn construct all sub components).
        Per
        """
        self._init_config()
        self._init_logging()
        self._init_state()
        self._init_main_components()
        self._init_settings()

    def _init_config(self):
        """Setup the config directory."""
        if not os.path.exists(constants.TEMP_IMAGES_DIRECTORY):
            os.mkdir(constants.TEMP_IMAGES_DIRECTORY)
            
    def _init_logging(self):
        """Setup logging for the application."""
        logging.config.fileConfig(constants.LOGGING_CONFIG)
        
    def _init_state(self):
        """Setup the state manager."""
        self._state_manager = GConfStateManager()
        
    def _init_main_components(self):
        """
        Create the main application components, which will
        request creation of other components as necessary.
        """
        self._main_model = MainModel(self)
        self._main_controller = MainController(self)
        self._main_view = MainView(self)
        
    def _init_settings(self):
        """
        Load current settings from the state manager and
        poll for available scanners.
        """
        self._main_model.load_state()        
        self._main_controller._update_available_scanners()
        
    # PUBLIC METHODS
        
    def run(self):
        """Execute the GTK main loop."""
        self._main_view.show()
        gtk.gdk.threads_init()
        gtk.main()
        
    def get_state_manager(self):
        """Return the L{GConfStateManager} component."""
        assert isinstance(self._state_manager, GConfStateManager)
        return self._state_manager
        
    def get_main_model(self):
        """Return the L{MainModel} component."""
        assert self._main_model
        return self._main_model
    
    def get_main_controller(self):
        """Return the L{MainController} component."""
        assert self._main_controller
        return self._main_controller
    
    def get_main_view(self):
        """Return the L{MainView} component."""
        assert self._main_view
        return self._main_view
    
    def get_preferences_model(self):
        """Return the L{PreferencesModel} component."""
        if not self._preferences_model:
            self._preferences_model = PreferencesModel(self)
        
        return self._preferences_model
    
    def get_preferences_controller(self):
        """Return the L{PreferencesController} component."""
        if not self._preferences_controller:            
            self._preferences_controller = PreferencesController(self)
                    
        return self._preferences_controller
    
    def get_preferences_view(self):
        """Return the L{PreferencesView} component."""
        if not self._preferences_view:            
            self._preferences_view = PreferencesView(self)
                    
        return self._preferences_view
    
    def show_preferences_dialog(self):
        """
        Show the preferences dialog.
        
        This is a convenience function.
        """
        self.get_preferences_view().show()
    
    def get_document_model(self):
        """Return the L{DocumentModel} component."""
        if not self._document_model:
            self._document_model = DocumentModel(self)
        
        return self._document_model
    
    def get_document_controller(self):
        """Return the L{DocumentController} component."""
        if not self._document_controller:            
            self._document_controller = DocumentController(self)
                    
        return self._document_controller
    
    def get_document_view(self):
        """Return the L{DocumentView} component."""
        if not self._document_view:            
            self._document_view = DocumentView(self)
                    
        return self._document_view
    
    def get_null_page_model(self):
        """
        Return an empty L{PageModel} object.
        
        This is the PageModel that is used when no
        pages have been scanned.
        """
        if not self._null_page_model:
            self._null_page_model = PageModel()
        
        return self._null_page_model
    
    def get_current_page_model(self):
        """
        Return the current/active L{PageModel} object.
        
        This is a convenience function.
        """
        return self.get_page_controller().get_current_page_model()
    
    def get_page_controller(self):
        """Return the L{PageController} component."""
        if not self._page_controller:            
            self._page_controller = PageController(self)
                    
        return self._page_controller
    
    def get_page_view(self):
        """Return the L{PageView} component."""
        if not self._page_view:            
            self._page_view = PageView(self)
                    
        return self._page_view
    
    def get_save_model(self):
        """Return the L{SaveModel} component."""
        if not self._save_model:
            self._save_model = SaveModel(self)
        
        return self._save_model
    
    def get_save_controller(self):
        """Return the L{SaveController} component."""
        if not self._save_controller:            
            self._save_controller = SaveController(self)
                    
        return self._save_controller
    
    def get_save_view(self):
        """Return the L{SaveView} component."""
        if not self._save_view:            
            self._save_view = SaveView(self)
                    
        return self._save_view
    
    def show_save_dialog(self):
        """
        Show the save dialog.
        
        This is a convenience function.
        """
        self.get_save_controller().run()
    
    def get_about_controller(self):
        """Return the L{SaveController} component."""
        if not self._about_controller:            
            self._about_controller = AboutController(self)
                    
        return self._about_controller
    
    def get_about_view(self):
        """Return the L{SaveView} component."""
        if not self._about_view:            
            self._about_view = AboutView(self)
                    
        return self._about_view
    
    def show_about_dialog(self):
        """
        Show the about dialog.
        
        This is a convenience function.
        """
        self.get_about_controller().run()
