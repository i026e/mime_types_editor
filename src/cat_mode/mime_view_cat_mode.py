#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 08:15:56 2016

@author: pavel
"""
import sys
sys.path.append('../common')

from gi.repository import Gtk, Gdk, Gio
from gi.repository import GdkPixbuf

import gtk_common
from gtk_common import ICON_SIZE

import mime_operations, mime_categories
import mime_view
import data_filter

from locale import gettext as _



class MimeViewCategories(mime_view.MimeView):
    UI_VIEW_ID = "mimetypes_view"
    UI_CONTEXT_MENU_ID = "mimeview_context_menu"

    #model columns
    MIME_TYPE = 0
    MIME_CATEGORY = 1
    MIME_DESC = 2
    MIME_ICON = 3

    MIME_APP = 4
    MIME_APP_IMG  = 5

    LIST_STORE_COLUMN_TYPES = [str, int, str, GdkPixbuf.Pixbuf,
                               str, GdkPixbuf.Pixbuf]

    def __init__(self, builder, on_items_edit, on_items_reset):
        """
            on_items_edit : function to call when edit action required
            on_items_reset : function to call when reset action required
        """
        self.on_items_edit = on_items_edit
        self.on_items_reset = on_items_reset

        super(MimeViewCategories, self).__init__(builder)
        self._init_buttons()

        self.set_data()

    def _init_buttons(self):
        reset_button = self.builder.get_object("reset_button")
        reset_button.connect("clicked", self.on_items_reset)

        edit_button = self.builder.get_object("edit_button")
        edit_button.connect("clicked",  self.on_items_edit)

    def _init_mappings(self):
        super(MimeViewCategories, self)._init_mappings()
        self.context_menu_items.update({"menuitem_revert": lambda *param : self.on_items_reset(),
                                   "menuitem_edit": lambda *param : self.on_items_edit(),
                                   })


        self.keyboard_keys_actions.update({"Return" : self.on_items_edit,
                                      "Enter" : self.on_items_edit,
                                      "space" : self.on_items_edit,
                                      "BackSpace" : self.on_items_reset,
                                      "Delete" : self.on_items_reset
                                      })


    def _init_columns(self, *args, **kwargs):
        self._add_filetype_column()
        self._add_app_column()

    def _add_app_column(self):
        column_program = gtk_common.ImageTextColumn(_("Program"), self.MIME_APP_IMG, self.MIME_APP)
        column_program.set_sort_column_id(self.MIME_APP)
        self.mtypes_view.append_column(column_program)

    def _init_filters(self):
        super(MimeViewCategories, self)._init_filters()


        associated_filter = data_filter.GeneralFilter(False, self.MIME_APP,
                                          lambda app : (app is not None) and (len(app) > 0))
        self._add_filter_to_cascade("associated_filter", associated_filter)


    def _get_model_data_row(self, mtype):
        mtype, category, descr, icon = super(MimeViewCategories, self)._get_model_data_row(mtype)

        app = mime_operations.get_default_app(mtype)
        app_name, app_icon, *extra = mime_operations.get_app_bio(app, ICON_SIZE)

        return [mtype, category, descr, icon, app_name, app_icon]


    def update_data(self, mtypes_to_change):
        tree_iter = self.list_store.get_iter_first()

        while tree_iter:
            row_mtype = self.list_store.get_value(tree_iter, self.MTYPE)

            if row_mtype in mtypes_to_change:
                app = mime_operations.get_default_app(row_mtype)
                name, icon, *extra = mime_operations.get_app_bio(app, ICON_SIZE)

                self.list_store.set_value(tree_iter, self.APP, name)
                self.list_store.set_value(tree_iter, self.APP_IMG, icon)

            tree_iter = self.list_store.iter_next(tree_iter)

    def filter_associated(self, show_all = True):
        self.set_filter_params("associated_filter",
                               enabled = not show_all)


    def on_double_click(self, widget, event):
        self.on_items_edit()


    def get_selection(self):
        """return mime types from selected rows"""
        return super(MimeViewCategories, self).get_selection(self.MIME_TYPE)
