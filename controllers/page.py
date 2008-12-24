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
This module holds the L{PageController}, which manages interaction 
between the L{PageModel} and L{PageView}.
"""

import logging

import gtk
from gtkmvc.controller import Controller

class PageController(Controller):
    """
    Manages interaction between the L{PageModel} and L{PageView}.
    """
    
    # SETUP METHODS
    
    def __init__(self, model):
        """
        Constructs the PageController.
        """
        Controller.__init__(self, model)

        self.log = logging.getLogger(self.__class__.__name__)
        
        # The preview pixbuf is cached so it can be rerendered without
        # reapplying zoom transformations.
        self.preview_pixbuf = None
        
        # Non persistent settings that apply to all scanned pages
        self.preview_width = 0
        self.preview_height = 0
        self.preview_zoom = 1.0
        self.preview_is_best_fit = False
        
        # TODO: should be a user preference
        self.preview_zoom_rect_color = \
            gtk.gdk.colormap_get_system().alloc_color(
                gtk.gdk.Color(65535, 0, 0), False, True)
                
        # Reusable temp vars to hold the start point of a mouse drag action.
        #self.preview_drag_start_x = 0
        #self.preview_drag_start_y = 0
        self.zoom_drag_start_x = 0
        self.zoom_drag_start_y = 0
        self.move_drag_start_x = 0
        self.move_drag_start_y = 0
        
        self.log.debug('Created.')

    def register_view(self, view):
        """
        Registers this controller with a view.
        """
        Controller.register_view(self, view)
        
        # TODO: temp
        #self._update_preview()
        
        self.log.debug('%s registered.', view.__class__.__name__)
        
    # USER INTERFACE CALLBACKS
    
    def on_page_view_image_layout_button_press_event(self, widget, event):
        """
        Begins a drag or zoom event.
        """        
        # Do not process mouse events if nothing is visible
        if not self.model.pixbuf:
            return
        
        if event.button == 1:
            self._begin_move(event.x, event.y)
        elif event.button == 3:
            self._begin_zoom(event.x, event.y)
    
    def on_page_view_image_layout_motion_notify_event(self, widget, event):
        """
        Update the preview during a drag or zoom event.
        """
        # Do not process mouse events if nothing is visible
        if not self.model.pixbuf:
            return
        
        # Handle both hint events and routine notifications
        # See: http://www.pygtk.org/pygtk2tutorial/sec-EventHandling.html
        if event.is_hint:
            mouse_state = event.window.get_pointer()[2]
        else:
            mouse_state = event.state
            
        # Move
        if (mouse_state & gtk.gdk.BUTTON1_MASK):
            self._update_move(event.x_root, event.y_root)
        # Zoom
        elif (mouse_state & gtk.gdk.BUTTON3_MASK):
            self._update_zoom(event.x, event.y)
        
        # NB: These need to be updated even if the button wasn't pressed
        self.move_drag_start_x = event.x_root
        self.move_drag_start_y = event.y_root
               
    def on_page_view_image_layout_button_release_event(self, widget, event):
        """
        Ends a drag or zoom event.
        """
        # Do not process mouse events if nothing is visible
        if not self.model.pixbuf:
            return
        
        # Move
        if event.button == 1:
            self._end_move()
        # Zoom
        elif event.button == 3:
            self._end_zoom(event.x, event.y)            
    
    def on_page_view_image_layout_scroll_event(self, widget, event):
        """
        TODO: Mouse scroll event.  Go to next/prev page?  Or scroll image?
        """
        pass
    
    def on_page_view_image_layout_size_allocate(self, widget, allocation):
        """
        Resizes the image preview size to match that which is allocated to
        the preview layout widget.
        
        TODO: Bug, when resizing window to be smaller (even slightly), the
        right scrollbar expands to take up ~20% of th preview space.
        """
        if allocation.width == self.preview_width and \
           allocation.height == self.preview_height:
            return
            
        self.preview_width = allocation.width
        self.preview_height = allocation.height

        self._update_preview()
#       self.update_status()
    
    # PROPERTY CALLBACKS
    
    def property_pixbuf_value_change(self, model, old_value, new_value):
        """
        Update the preview display.
        """
        self._update_preview()
#       self.update_status()
    
    # PUBLIC METHODS
    
    def set_model(self, page_model):
        """
        Sets the PageModel that is currently being displayed in the preview area.
        """
        self.model.unregister_observer(self)
        self.model = page_model
        self.model.register_observer(self)
        
        self._update_preview()
    
    def zoom_in(self):
        """
        Zooms the preview image in.
        """ 
        # TODO: max zoom should be configurable
        if self.preview_zoom == 5:
            return
        
        # TODO: zoom amount should be configurable
        self.preview_zoom +=  0.5
        
        if self.preview_zoom > 5:
            self.preview_zoom = 5
            
        self.preview_is_best_fit = False
            
        self._update_preview()
        #self.update_status()
    
    def zoom_out(self):  
        """
        Zooms the preview image out.
        """             
        if self.preview_zoom == 0.5:
            return
            
        self.preview_zoom -=  0.5
        
        if self.preview_zoom < 0.5:
            self.preview_zoom = 0.5
            
        self.preview_is_best_fit = False
            
        self._update_preview()
        #self.update_status()
    
    def zoom_one_to_one(self):
        """
        Zooms the preview image to its true size.
        """
        self.preview_zoom =  1.0
        self.preview_is_best_fit = False
            
        self._update_preview()
        #self.update_status()
    
    def zoom_best_fit(self):
        """
        Zooms the preview image so the entire image will fit within the
        preview window.
        """   
        self.preview_is_best_fit = True

        self._update_preview()
        #self.update_status()
        
    def rotate_counter_clockwise(self):
        #TODO
        self.model.rotate_counter_clockwise()
    
    def rotate_clockwise(self):
        #TODO
        self.model.rotate_clockwise()
    
    # PRIVATE (INTERNAL) METHODS
    
    def _begin_move(self, x, y):
        """
        Determines if there is anything to be dragged and if so, sets the
        'drag' cursor.
        """
        if self.view['page_view_horizontal_scrollbar'].get_property('visible') and \
           self.view['page_view_vertical_scrollbar'].get_property('visible'):
               return
           
        self.view['page_view_image'].get_parent_window().set_cursor(
            gtk.gdk.Cursor(gtk.gdk.FLEUR))
                
    def _begin_zoom(self, x, y):
        """
        Saves the starting position of the zoom and sets the 'zoom' cursor.
        """
        self.view['page_view_image'].get_parent_window().set_cursor(
            gtk.gdk.Cursor(gtk.gdk.CROSS))
            
        self.zoom_drag_start_x = x
        self.zoom_drag_start_y = y
            
    def _update_move(self, x, y):
        """
        Moves/drags the preview in response to mouse movement.
        """
        horizontal_adjustment = \
            self.view['page_view_image_layout'].get_hadjustment()
        
        new_x = horizontal_adjustment.value + \
            (self.move_drag_start_x - x)
                        
        if new_x >= horizontal_adjustment.lower and \
           new_x <= horizontal_adjustment.upper - horizontal_adjustment.page_size:
            horizontal_adjustment.set_value(new_x)
            
        vertical_adjustment = \
            self.view['page_view_image_layout'].get_vadjustment()
            
        new_y = vertical_adjustment.value + \
                (self.move_drag_start_y - y)
        
        if new_y >= vertical_adjustment.lower and \
           new_y <= vertical_adjustment.upper - vertical_adjustment.page_size:
            vertical_adjustment.set_value(new_y)
    
    def _update_zoom(self, x, y):
            """
            Renders a box around the zoom region the user has specified
            by dragging the mouse.
            """
            start_x = self.zoom_drag_start_x
            start_y = self.zoom_drag_start_y
            end_x = x
            end_y = y
            
            if end_x < start_x:
                start_x, end_x = end_x, start_x
                
            if end_y < start_y:
                start_y, end_y = end_y, start_y
            
            width = end_x - start_x
            height = end_y - start_y

            self.view['page_view_image'].set_from_pixbuf(self.preview_pixbuf)
            self.view['page_view_image'].get_parent_window().invalidate_rect(
                (0, 0, self.preview_width, self.preview_height), 
                False)
            self.view['page_view_image'].get_parent_window(). \
                process_updates(False)
            
            graphics_context = \
                self.view['page_view_image'].get_parent_window().new_gc(
                    foreground=self.preview_zoom_rect_color, 
                    line_style=gtk.gdk.LINE_ON_OFF_DASH, 
                    line_width=2)
                
            self.view['page_view_image'].get_parent_window().draw_rectangle(
                graphics_context, 
                False, 
                int(start_x), int(start_y), 
                int(width), int(height))
            
    def _end_move(self):
        """
        Resets to the default cursor.
        """
        self.view['page_view_image'].get_parent_window().set_cursor(None)
        
    def _end_zoom(self, x, y):
        """
        Calculates and applies zoom to the preview and updates the display.
        """        
        # Transform to absolute coords
        start_x = self.zoom_drag_start_x / self.preview_zoom
        start_y = self.zoom_drag_start_y / self.preview_zoom
        end_x = x / self.preview_zoom
        end_y = y / self.preview_zoom
        
        # Swizzle values if coords are reversed
        if end_x < start_x:
            start_x, end_x = end_x, start_x
            
        if end_y < start_y:
            start_y, end_y = end_y, start_y
        
        # Calc width and height
        width = end_x - start_x
        height = end_y - start_y
        
        # Calculate centering offset
        target_width =  \
            self.model.width * self.preview_zoom
        target_height = \
            self.model.height * self.preview_zoom
        
        shift_x = int((self.preview_width - target_width) / 2)
        if shift_x < 0:
            shift_x = 0
        shift_y = int((self.preview_height - target_height) / 2)
        if shift_y < 0:
            shift_y = 0
        
        # Compensate for centering
        start_x -= shift_x / self.preview_zoom
        start_y -= shift_y / self.preview_zoom
        
        # Determine center-point of zoom region
        center_x = start_x + width / 2
        center_y = start_y + height / 2
        
        # Determine correct zoom to fit region
        if width > height:
            self.preview_zoom = self.preview_width / width
        else:
            self.preview_zoom = self.preview_height / height
            
        # Cap zoom at 500%
        if self.preview_zoom > 5.0:
            self.preview_zoom = 5.0
            
        # Transform center-point to relative coords            
        transform_x = int(center_x * self.preview_zoom)
        transform_y = int(center_y * self.preview_zoom)
        
        # Center in preview display
        transform_x -= int(self.preview_width / 2)
        transform_y -= int(self.preview_height / 2)
        
        self.preview_is_best_fit = False
        self._update_preview()
        
        self.view['page_view_image_layout'].get_hadjustment().set_value(
            transform_x)
        self.view['page_view_image_layout'].get_vadjustment().set_value(
            transform_y)
        
        #self.update_status()
        
        self.view['page_view_image'].get_parent_window().set_cursor(None)        
        
    def _update_preview(self):
        """
        Render the current page to the preview display.
        """
        # Short circuit if the view has not been created yet.
        if not self.view:
            return
        
        # Short circuit if the PageModel does not have a pixbuf 
        # (such as DocumentModel.null_page).
        if not self.model.pixbuf:
            self.view['page_view_image'].clear()
            return
        
        # Fit if necessary
        if self.preview_is_best_fit:
            width_ratio = float(self.model.width) / self.preview_width
            height_ratio = float(self.model.height) / self.preview_height
            
            if width_ratio < height_ratio:
                self.preview_zoom =  1 / float(height_ratio)
            else:
                self.preview_zoom =  1 / float(width_ratio)
        
        # Zoom if necessary
        if self.preview_zoom != 1.0:
            target_width = \
                int(self.model.width * self.preview_zoom)
            target_height = \
                int(self.model.height * self.preview_zoom)
            
            self.preview_pixbuf = self.model.pixbuf.scale_simple(
                target_width, target_height, gtk.gdk.INTERP_BILINEAR)
        else:
            target_width = self.model.width
            target_height = self.model.height
        
            self.preview_pixbuf = self.model.pixbuf
        
        # Resize preview area
        self.view['page_view_image_layout'].set_size(
            target_width, target_height)
        
        # Center preview
        shift_x = int((self.preview_width - target_width) / 2)
        if shift_x < 0:
            shift_x = 0
        shift_y = int((self.preview_height - target_height) / 2)
        if shift_y < 0:
            shift_y = 0
        self.view['page_view_image_layout'].move(
            self.view['page_view_image'], shift_x, shift_y)
        
        # Show/hide scrollbars
        if target_width > self.preview_width:
            self.view['page_view_horizontal_scrollbar'].show()
        else:
            self.view['page_view_horizontal_scrollbar'].hide()
            
        if target_height > self.preview_height:
            self.view['page_view_vertical_scrollbar'].show()
        else:
            self.view['page_view_vertical_scrollbar'].hide()
        
        # Render updated preview
        self.view['page_view_image'].set_from_pixbuf(self.preview_pixbuf)
