#!/usr/bin/python
#
# Gedit Split View
# https://github.com/jonocodes/GeditSplitView
#
# Copyright (C) Mike Doty 2010 and Jono Finger 2012 <jono@foodnotblogs.com>
# 
# The program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# The program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
import urllib

from gi.repository import Gtk, Gedit, GObject

ui_string = """<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
      <placeholder name="ViewOps_2">
        <menuitem name="ExamplePy" action="ExamplePy"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class PluginHelper:
    def __init__(self, plugin, window):
        self.window = window
        self.plugin = plugin

        self.document_list = []

        self.ui_id = None

        # Add a "toggle split view" item to the View menu
        self.insert_menu_item(window)

        # We're going to keep track of each tab's split view. We'll
        # index each dictionary via the tab objects.
        self.split_views = {}

        self.tabs_already_using_splitview = []

        # I hardly even know how this works, but it gets our encoding.
        try: self.encoding = Gedit.encoding_get_current()
        except: self.encoding = Gedit.gedit_encoding_get_current()
        
    def deactivate(self):
        print ("deactivate")
        self.remove_menu_item()

        self.window = None
        self.plugin = None
        
    def update_ui(self):
        return

    def toggle_split_view(self, unused):

        current_tab = self.window.get_active_tab()

        if (current_tab in self.split_views):
            self.end_split_view(None)
        else:
            self.split_view(None)

    # This function creates the split view.
    def split_view(self, whatever = None, direction = "vertical", changing = False):

        print ('split_view')

        # Get the tab / document
        current_tab = self.window.get_active_tab()
        current_document = self.window.get_active_document()

        if (not changing):

            if (current_tab in self.tabs_already_using_splitview):
                return

            else:
                self.tabs_already_using_splitview.append( current_tab )

        old_other_view = None
        if (current_tab in self.split_views):
            old_other_view = self.split_views[current_tab].get_child2()

        # Create a new HPaned or VPaned object for the splitview.
        if (direction == "vertical"):
            self.split_views[current_tab] = Gtk.HPaned()

        else:
            self.split_views[current_tab] = Gtk.VPaned()

        old_view = None

        # Here we just kind of loop through the child object of the tab
        # and get rid of all of the existing GUI objects.
        for each in current_tab.get_children():

            # The child of the child has the View object for the active document.
            for any in each.get_children():

                old_view = any
                each.remove(any)

            # Create a scrolled window for the left / top side.
            sw1 = Gtk.ScrolledWindow()
            sw1.add_with_viewport(old_view)

            # Set up a new View object
            new_view = Gedit.View.new(current_document)

            # Second scrolled window.
            sw2 = Gtk.ScrolledWindow()
            sw2.add_with_viewport(new_view)

            # Add the two scrolled windows to our Paned object.
            self.split_views[current_tab].add1(sw1)
            self.split_views[current_tab].add2(sw2)

            # The next few lines of code just create some buttons.
            hbox = Gtk.HBox()

            self.btn_cancel = Gtk.Button("End Splitview")
            self.btn_cancel.connect("clicked", self.end_split_view)

            self.btn_flip = Gtk.Button("Vertical Splitview")
            self.btn_flip.connect("clicked", self.flip_split_view)

            hbox.pack_start(self.btn_cancel, False, False, 0)
            hbox.pack_start(self.btn_flip, False, False, 0)

            vbox = Gtk.VBox()

            vbox.pack_start(hbox, False, False, 0)
            vbox.pack_start(self.split_views[current_tab], True, True, 0)

            each.add(vbox)

            # The trick of this whole thing is that you have to wait a second for the
            # Paned object to figure out how much room it can take up.  So, we're just
            # going to set a timer that'll check every 500 milliseconds until it
            # decides it can trust the width that the Paned object returns.
            GObject.timeout_add(500, self.debug)

        current_tab.show_all()

    # This of course ends the split view... though I call this when switching
    # from left / right to top / bottom or vice versa.  If I'm doing that then
    # changing will be True I believe.
    def end_split_view(self, unused, changing=False):
        current_tab = self.window.get_active_tab()
        current_document = current_tab.get_document()

        original_view = self.split_views[current_tab].get_child1().get_children()[0]

        for each in current_tab.get_children():

            for any in each.get_children():
                each.remove(any)

            original_view.reparent(each)

        current_tab.show_all()

        self.split_views.pop(current_tab)

        if (not changing):
            
            if (current_tab in self.tabs_already_using_splitview):
                index = self.tabs_already_using_splitview.index(current_tab)

                self.tabs_already_using_splitview.pop(index)

    # Basically recreate the split view.
    def flip_split_view(self, button):
        if (self.btn_flip.get_label() == "Vertical Splitview"):
            self.end_split_view(None, changing = True)
            self.split_view(None, "horizontal", changing = True)

            self.btn_flip.set_label("Horizontal Splitview")

        else:
            self.end_split_view(None, changing = True)
            self.split_view(None, "vertical", changing = True)

            self.btn_flip.set_label("Vertical Splitview")

        current_tab = self.window.get_active_tab()

    # This function eventually sets the divider of the splitview at 50%.
    # It waits until the gui object returns a reasonable width.
    def debug(self):
        current_tab = self.window.get_active_tab()

        x = self.split_views[current_tab].get_property("max-position")

        # At first it just says 0 or 1 ... I just picked 50 at random.  If you're using GEdit
        # and you have a viewable editing window of < 50 pixels, then, uh, sorry!
        if (x > 50):
            self.split_views[current_tab].set_position(x / 2)

            return False

        return True

    def insert_menu_item(self, window):
        manager = self.window.get_ui_manager()
        
        self.action_group = Gtk.ActionGroup("PluginActions")
        
        # Create an action for the "Run in python" menu option
        # and set it to call the "run_document_in_python" function.
        self.split_view_action = Gtk.Action(name="ExamplePy", label="Toggle Split View", tooltip="Create a split view of the current document", stock_id=Gtk.STOCK_REFRESH)
        self.split_view_action.connect("activate", self.toggle_split_view)
        
        # Add the action with Ctrl + F5 as its keyboard shortcut.
        self.action_group.add_action_with_accel(self.split_view_action, "<Ctrl><Shift>T")

        # Add the action group.
        manager.insert_action_group(self.action_group, -1)

        # Add the item to the "Views" menu.
        self.ui_id = manager.add_ui_from_string(ui_string)

        manager.ensure_update()
        
    def remove_menu_item(self):
        panel = self.window.get_side_panel()
        
        manager = self.window.get_ui_manager()

        manager.remove_ui(self.ui_id)

        self.ui_id = None


class WindowActivatable(GObject.Object, Gedit.WindowActivatable):

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self.instances = {}
        
    def do_activate(self):
        self.instances[self.window] = PluginHelper(self, self.window)
        
    def do_deactivate(self):
        if self.window in self.instances:
            self.instances[self.window].deactivate()
        
    def update_ui(self):
        if self.window in self.instances:
            self.instances[self.window].update_ui()

