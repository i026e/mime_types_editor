#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 25 07:18:57 2016

@author: pavel
"""

import mime_categories
import mime_operations

from gi.repository import Gtk
from gi.repository import GdkPixbuf
from locale import gettext as _

ICON_SIZE = 24

def browse_for_file(title, start_directory, parent_window, on_success_callback):
    f_dialog = Gtk.FileChooserDialog(title,
                                     action = Gtk.FileChooserAction.OPEN,
                                     buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                                  Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
    f_dialog.set_current_folder(start_directory)
    f_dialog.set_transient_for(parent_window)

    if f_dialog.run() == Gtk.ResponseType.ACCEPT:
        on_success_callback(f_dialog.get_filename())

    f_dialog.destroy()

class ImageTextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, model_index_img, model_index_txt, *args, **kwargs):
        super(ImageTextColumn, self).__init__(column_name, *args, **kwargs)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_text = Gtk.CellRendererText()
        self.cell_renderers = (renderer_pixbuf, renderer_text, )

        self.pack_start(renderer_pixbuf, expand = False)
        self.add_attribute(renderer_pixbuf, "pixbuf", model_index_img)

        self.pack_start(renderer_text, expand = True)
        self.add_attribute(renderer_text, "text", model_index_txt)

        self.set_resizable(True)

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)


class TextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, model_index_txt, *args, **kwargs):
        super(TextColumn, self).__init__(column_name, *args, **kwargs)
        renderer_text = Gtk.CellRendererText()
        self.cell_renderers = (renderer_text, )

        self.pack_start(renderer_text, expand = True)
        self.add_attribute(renderer_text, "text", model_index_txt)

        self.set_resizable(True)



    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)

class FlagColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, model_index_bool, on_toggle, on_mark_all,
                                                             *args, **kwargs):
        super(FlagColumn, self).__init__(None, *args, **kwargs)

        self.header_checkbox = CyclicCheckbox(on_mark_all)
        self.title = Gtk.Label(column_name)

        self.header_widget = Gtk.HBox()
        self.header_widget.pack_start(self.header_checkbox, True, True, 0)
        self.header_widget.pack_start(self.title, True, True, 0)
        self.header_widget.show_all()
        self.set_widget(self.header_widget)


        renderer_flag = Gtk.CellRendererToggle()
        self.cell_renderers = (renderer_flag, )

        renderer_flag.connect("toggled", on_toggle)

        self.pack_start(renderer_flag, expand = False)
        self.add_attribute(renderer_flag, "active", model_index_bool)

        self.set_clickable(True)
        self.set_resizable(False)
        self.connect("clicked", self.header_checkbox.on_click)


        #self.set_sort_indicator(True)


    #def on_header_clicked(self, *args):
    #    self.header_checkbox.on_click()


    def set_flag_degenerate(self, degenerate):
        self.header_checkbox.set_degenerate(degenerate)
    def set_flag_inconsistent(self):
        self.header_checkbox.set_inconsistent()
    def set_flag_active(self, *args):
        self.header_checkbox.set_active(*args)
    def set_flag_inactive(self):
        self.header_checkbox.set_inactive()

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)


class CyclicCheckbox(Gtk.CheckButton):
    STATE_ACTIVE = 0
    STATE_INACTIVE = 1
    STATE_INCONSISTENT = 2


    def __init__(self, on_state_change, *args, **kwargs):
        super(CyclicCheckbox, self).__init__(None, *args, **kwargs)
        self.on_state_change = on_state_change

        #self.connect("clicked", self.on_click)

        self.set_degenerate(False)
        self.set_inactive()

    def on_click(self, *args):
        self.next_state()
        self.on_state_change(self.get_inconsistent(), self.get_active())

        return False

    def next_state(self):
        if self.state == CyclicCheckbox.STATE_ACTIVE:
            self.set_inactive()
        elif self.state == CyclicCheckbox.STATE_INACTIVE:
            if self.degenerate: # skip inconsistent
                self.set_active()
            else:
                self.set_inconsistent()
        else:
            self.set_active()

    def set_degenerate(self, degenerate = False):
        # if degenerate, then inconsistent state will be in cycle
        self.degenerate = degenerate


    def set_inconsistent(self):
        #print("inconsistent")
        self.state = CyclicCheckbox.STATE_INCONSISTENT

        super(CyclicCheckbox, self).set_inconsistent(True)
        super(CyclicCheckbox, self).set_active(False)

    def set_active(self, active = True):
        #print("active")
        if active:
            self.state = CyclicCheckbox.STATE_ACTIVE

            super(CyclicCheckbox, self).set_inconsistent(False)
            super(CyclicCheckbox, self).set_active(True)
        else:
            self.set_inactive()

    def set_inactive(self):
        #print("inactive")
        self.state = CyclicCheckbox.STATE_INACTIVE

        super(CyclicCheckbox, self).set_inconsistent(False)
        super(CyclicCheckbox, self).set_active(False)



class IconTextLabel(Gtk.Box):
    def __init__(self, icon, text, *args, **kwargs):
        super( IconTextLabel, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)

        label = Gtk.Label(text)

        self.pack_start(icon, True, True, 0)
        self.pack_start(label, True, True, 0)

class CategoriesWidget:
    CAT_ID = 0
    CAT_NAME = 1
    CAT_IMG = 2

    def __init__(self, builder, widget_name, on_category_changed):
        self.widget = builder.get_object(widget_name)
        self.on_category_changed = on_category_changed

        self._init_model()
        self._init_widget()

        self._set_data()

    def _init_model(self):
        self.list_store = Gtk.ListStore(int,  str, GdkPixbuf.Pixbuf)
        self.widget.set_model(self.list_store)

    def _init_widget(self):
        raise NotImplemented

    def _set_data(self):
        categories = sorted((_(name), cat ,id_)
                            for cat, name, id_ in mime_categories.get_known_categories())

        # should be last
        categories.append((_(mime_categories.ANY_CATEGORY_NAME),
                          mime_categories.ANY_CATEGORY,
                          mime_categories.ANY_CATEGORY_ID))


        for transl_name, cat, id_ in categories:
            icon_name = mime_categories.get_icon_name(cat)
            icon = mime_operations.get_icon_by_name(icon_name, ICON_SIZE)
            self.list_store.append([id_, transl_name, icon])



