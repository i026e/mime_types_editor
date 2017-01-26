#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 08:15:56 2016

@author: pavel
"""
import mime_operations, mime_categories
import data_filter

from gi.repository import Gtk, Gdk, Gio, GObject
from gi.repository import GdkPixbuf

from gtk_common import ImageTextColumn, FlagColumn, TextColumn
from gtk_common import ICON_SIZE

from locale import gettext as _
from threading import Thread



class MimeView:
    UI_VIEW_ID = None
    UI_CONTEXT_MENU_ID = None

    #model columns
    MIME_TYPE = 0
    MIME_CATEGORY = 1
    MIME_DESC = 2
    MIME_ICON = 3
    LIST_STORE_COLUMN_TYPES = [str, int, str, GdkPixbuf.Pixbuf]


    def __init__(self, builder):
        self.builder = builder

        self.mtypes_view = self.builder.get_object(self.UI_VIEW_ID)

         #callbacks
        self.mtypes_view.connect("button-press-event", self.on_mouse_clicked)
        self.mtypes_view.connect("key-press-event", self.on_key_pressed)

        #allow multiple selection
        self.tree_selection = self.mtypes_view.get_selection()
        self.tree_selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self._init_mappings()
        self._init_filters()

        self._init_model()
        self._init_columns()
        self._init_context_menu()

    def _init_mappings(self):
        #mappings
        self.context_menu_items = {} # dictionary of item_id: item_action pairs
        self.keyboard_keys_actions = {"Menu" : self.show_context_menu
                                      } # dictionary of key_name: key_action pairs

    def _init_filters(self):
        self.ordered_data_filters = [] #order may be matter
        self.data_filters = {} # save reference by name

        #add category filter
        category_filter = data_filter.CategoryFilter(self.MIME_CATEGORY,
                                            mime_categories.ANY_CATEGORY_ID)

        self._add_filter_to_cascade("category_filter", category_filter)

    def _add_filter_to_cascade(self, filter_name, data_filter):
        self.ordered_data_filters.append(data_filter)
        self.data_filters[filter_name] = data_filter

    def _init_model(self):
        """liststore -> filter -> sort -> view"""
        self.list_store = Gtk.ListStore(*self.LIST_STORE_COLUMN_TYPES)

        self.filter_model = self.list_store.filter_new()
        self.filter_model.set_visible_func(self.cascade_filter_func, data=None)

        self.sortable_model = Gtk.TreeModelSort(self.filter_model)

        self.mtypes_view.set_model(self.sortable_model)

    def _init_columns(self):
        self._add_filetype_column()

    def _init_context_menu(self):
        self.context_menu = self.builder.get_object(self.UI_CONTEXT_MENU_ID)

        for item_id, action in self.context_menu_items.items():
            item = self.builder.get_object(item_id)
            item.connect("activate", action)


    def set_data(self, *args, **kwargs):
        def background_job():
            mtypes = self._get_initial_data(*args, **kwargs)
            GObject.idle_add(self._add_mtypes, mtypes)

        self.list_store.clear()
        self.thread = Thread(target = background_job)
        self.thread.start()

    def set_filter_params(self, filter_name, **kwargs):
        if filter_name in self.data_filters:
            self.data_filters[filter_name].set_params(**kwargs)

        self.filter_model.refilter()

    def _add_mtypes(self, mtypes, *args, **kwargs):
        for mtype in mtypes:
            data_row = self._get_model_data_row(mtype, *args, **kwargs)
            self.list_store.append(data_row)

    def _get_initial_data(self, *args, **kwargs):
        return mime_operations.get_known_mtypes()

    def _add_filetype_column(self):
        self.desc_column = ImageTextColumn(_("File Type"), self.MIME_ICON, self.MIME_DESC)
        self.desc_column.set_sort_column_id(self.MIME_DESC)
        self.mtypes_view.append_column(self.desc_column)


    def _get_model_data_row(self, mtype):
        descr, icon = mime_operations.get_mime_bio(mtype, ICON_SIZE)
        category = mime_categories.get_category_id(mtype)
        return [mtype, category, descr, icon]

    def cascade_filter_func(self, model, iter_, data):
        # return True if all conditions are satisfied
        for filter_ in self.ordered_data_filters:
            if not filter_.process_row(model, iter_, data):
                return False
        return True

    def on_mouse_clicked(self, widget, event):
        if event.button == 3: #right button
            self.show_context_menu(widget, event)
            return True
        if event.type == Gdk.EventType._2BUTTON_PRESS: #double click
            self.on_double_click(widget, event)
            return True

    def on_key_pressed(self, widget, event):
        #do not reset selection
        keyname = Gdk.keyval_name(event.keyval)
        print(keyname, "button pressed")

        if keyname in self.keyboard_keys_actions:
            #execute
            self.keyboard_keys_actions.get(keyname, print)(widget, event)
            return True

    def on_double_click(self, widget, event):
        raise NotImplemented


    def show_context_menu(self, widget, event):
        self.context_menu.popup( None, None, None, None, 0, event.time)


    def get_store_path(self, sorted_path):
        """applying filters and sorting cause problem that
        selection path does not correspond store path any more"""

        filtered_path = self.sortable_model.convert_path_to_child_path(sorted_path)
        store_path = self.filter_model.convert_path_to_child_path(filtered_path)

        #print(sorted_path, filtered_path, store_path)
        return store_path

    def get_new_value(self, model, tree_iter, get_value_func = None,
                      value = None, **kwargs):
        if get_value_func is not None:
            value = get_value_func(model, tree_iter, **kwargs)

        return value

    def iterate_all(self):
        tree_iter = self.list_store.get_iter_first()
        while tree_iter:
            yield self.list_store, tree_iter

            tree_iter = self.list_store.iter_next(tree_iter)

    def iterate_visible(self):
        tree_iter = self.list_store.get_iter_first()
        while tree_iter:
            if self.cascade_filter_func(self.list_store, tree_iter, None):
                yield self.list_store, tree_iter
            tree_iter = self.list_store.iter_next(tree_iter)

    def iterate_selected(self):
        (model, pathlist) = self.tree_selection.get_selected_rows()

        for path in pathlist :
            tree_iter = self.list_store.get_iter(self.get_store_path(path))
            yield self.list_store, tree_iter

    def iterate_by_values(self, column, values):
        tree_iter = self.list_store.get_iter_first()
        while tree_iter:
            val = self.list_store.get_value(tree_iter, column)
            if val in values:
                yield self.list_store, tree_iter
            tree_iter = self.list_store.iter_next(tree_iter)

    def set_value_if_cond(self, model, tree_iter, column,
                         get_value_func = None, value = None,
                         conditions_func = None, **kwargs):
        """column = column to change value
           get_value_func = function to compute new value depending on row
                           should accept model and iter as parameters
           value = value to set if get_value_func is not specified
           extra_conditions_func = function to check if possible to set new value
        """
        if conditions_func is None or \
        conditions_func(model, tree_iter, **kwargs):
            value = self.get_new_value(self.list_store, tree_iter,
                                       get_value_func, value, **kwargs)
            model.set_value(tree_iter, column, value)


    def set_value_to_all(self, column,
                         get_value_func = None, value = None,
                         conditions_func = None, **kwargs):

        for (model, iter_) in self.iterate_all():
            self.set_value_if_cond(model, iter_, column,
                                   get_value_func, value,
                                   conditions_func, **kwargs)


    def set_value_to_selected(self, column,
                         get_value_func = None, value = None,
                         conditions_func = None, **kwargs):

        for (model, iter_) in self.iterate_selected():
            self.set_value_if_cond(model, iter_, column,
                                   get_value_func, value,
                                   conditions_func, **kwargs)


    def set_value_to_visible(self, column,
                         get_value_func = None, value = None,
                         conditions_func = None, **kwargs):

        for (model, iter_) in self.iterate_visible():
            self.set_value_if_cond(model, iter_, column,
                                   get_value_func, value,
                                   conditions_func, **kwargs)

    def get_selection(self, column):
        selection = []

        for (model, iter_) in self.iterate_selected():
            selection.append(model.get_value(iter_, column))

        return selection

    def filter_category(self, category_id = mime_categories.ANY_CATEGORY_ID):
        self.set_filter_params("category_filter",
                               current_category_id = category_id)
