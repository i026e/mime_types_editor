#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 06:50:25 2016

@author: pavel
"""
import os
DIR = os.path.dirname(os.path.realpath(__file__))

import sys
sys.path.append(os.path.join(DIR, '../common'))

from gi.repository import Gtk, Gdk, Gio
from gi.repository import GdkPixbuf

from locale import gettext as _

import mime_operations
import mime_categories
import mime_view_cat_mode

import gtk_common
from gtk_common import browse_for_file
from gtk_common import ICON_SIZE


GLADE_FILE = os.path.join(DIR,"ui_cat_mode.glade")
SHOW_ONLY_ASSOCIATED = True

class CategoriesView(gtk_common.CategoriesWidget):
    CAT_ID = 0
    CAT_NAME, CAT_IMG = 1, 2


    def __init__(self, builder, on_category_changed):
        """ on_category_changed : called every time category is changed,
            should accept list of category ids"""
        self.categories_view = builder.get_object("categories_view")
        self.on_category_changed = on_category_changed

        # id, name, img
        self.list_store = Gtk.ListStore(int,  str, GdkPixbuf.Pixbuf)
        self.categories_view.set_model(self.list_store)

        self._fill_list_store()

        column = gtk_common.ImageTextColumn(_("Categories"), self.CAT_IMG, self.CAT_NAME)
        self.categories_view.append_column(column)

        #register callback
        tree_selection = self.categories_view.get_selection()
        tree_selection.connect("changed", self.on_selection_changes)

    def _fill_list_store(self):
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

    def on_selection_changes(self, tree_selection):
        (model, pathlist) = tree_selection.get_selected_rows()
        cat_ids = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, self.CAT_ID)
            cat_ids.append(value)
        self.on_category_changed(cat_ids)



class AddAppDialog:
    def __init__(self, builder, parent_window, on_add_dialog_apply):
        self.builder = builder
        self.on_add_dialog_apply = on_add_dialog_apply

        self.dialog = self.builder.get_object("add_app_dialog")
        self.app_chooser = self.builder.get_object("appchooser_widget")
        self.app_chooser.set_show_all(True)
        self.app_chooser.connect("application-activated", self.on_apply)
        self.app_chooser.connect("application-selected", self.on_application_selected)

        self.dialog.set_transient_for(parent_window)
        self.dialog.connect("delete-event", self.hide)

        self.custom_entry = self.builder.get_object("custom_entry")
        self.custom_entry.connect("changed", self.on_custom_entry_changed)

        self.selected_app = None
        self.cline_text = ""

        self._init_buttons()

    def _init_buttons(self):
        self.cancel_button = self.builder.get_object("add_app_dialog_cancel_button")
        self.apply_button = self.builder.get_object("add_app_dialog_apply_button")
        self.file_chooser_button = self.builder.get_object("file_chooser_button")

        self.cancel_button.connect("clicked", self.hide)
        self.apply_button.connect("clicked", self.on_apply)
        self.file_chooser_button.connect("clicked", self.on_file_chooser)

    def show(self):
        self.dialog.run()

    def hide(self, *args):
        self.dialog.hide()

        return False #!!!

    def on_custom_entry_changed(self, *args):
        text = self.custom_entry.get_text()
        if text != self.cline_text:
            self.cline_text = text

            self.selected_app = mime_operations.get_app_from_cline(self.cline_text,
                                                                   None)

    def on_application_selected(self, widget, app):
        self.selected_app = app

        name, icon, self.cline_text =  mime_operations.get_app_bio(app, ICON_SIZE)
        self.custom_entry.set_text(self.cline_text)

    def on_file_chooser(self, *args):
        browse_for_file(_('Choose an application'),
                        '/usr/bin',
                        self.dialog,
                        self.custom_entry.set_text)

    def on_apply(self, *args):
        #“application-activated”
        self.on_add_dialog_apply(self.selected_app)
        self.hide()


class MimeSetDialog:
    APP_OBJ = 0
    APP_NAME = 1
    APP_ICON = 2
    APP_CL = 3

    def __init__(self, builder, parent_window, on_dialog_ok):
        self.builder = builder

        self.on_dialog_ok = on_dialog_ok

        self.dialog = self.builder.get_object("mimetype_set_dialog")
        self.dialog.set_transient_for(parent_window)
        self.dialog.connect("delete-event", self.hide)

        self.mtypes_dialog_label = builder.get_object("mtypes_dialog_label")

        self._init_buttons()
        self._init_view()
        self.add_app_dialog = None

        #
        self.mtypes = []

    def _init_buttons(self):
        self.cancel_button = self.builder.get_object("dialog_cancel_button")
        self.apply_button = self.builder.get_object("dialog_apply_button")
        self.add_button = self.builder.get_object("dialog_add_button")

        self.cancel_button.connect("clicked", self.hide)
        self.apply_button.connect("clicked", self.on_row_activated)
        self.add_button.connect("clicked", self.on_add_app_clicked)

    def _init_view(self):
        self.alt_view = self.builder.get_object("alternatives_treeview")
        self.alt_view.connect("row_activated", self.on_row_activated)

        # desktop_file, app_name, icon
        self.list_store = Gtk.ListStore(Gio.AppInfo, str ,GdkPixbuf.Pixbuf, str)

        self.alt_view.set_model(self.list_store)

        column_app = gtk_common.ImageTextColumn(_("Application"), self.APP_ICON, self.APP_NAME)
        column_app.set_sort_column_id(self.APP_NAME)

        self.alt_view.append_column(column_app)

        column_cl = gtk_common.TextColumn(_("Command line"), self.APP_CL)
        column_cl.set_sort_column_id(self.APP_CL)

        self.alt_view.append_column(column_cl)

    def show(self, mtypes):
        self.mtypes = mtypes
        self.set_data()
        self.indicate_default()

        self.mtypes_dialog_label.set_text(" \n".join(self.mtypes))

        self.dialog.run()

    def hide(self, *args):
        self.dialog.hide()
        self.list_store.clear()

        return True #!!!

    def set_data(self):
        #if self.vbox is not None: return
        apps = mime_operations.get_apps_for_mtypes(self.mtypes)

        for app in apps:
            name, icon, cl =  mime_operations.get_app_bio(app, ICON_SIZE)

            self.list_store.append([app, name, icon, cl])

    def indicate_default(self):
        if len(self.mtypes) == 1:
            default_app = mime_operations.get_default_app(self.mtypes[0])
            default_cl = default_app.get_commandline() if default_app is not None else ""

            #iteratw
            tree_iter = self.list_store.get_iter_first()
            while tree_iter:
                current_cl = self.list_store.get_value(tree_iter, self.APP_CL)

                if current_cl == default_cl:
                    self.alt_view.get_selection().select_iter(tree_iter)
                    return
                tree_iter = self.list_store.iter_next(tree_iter)


    def on_row_activated(self, *args):
        tree_selection = self.alt_view.get_selection()
        (model, pathlist) = tree_selection.get_selected_rows()

        selection = None

        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, self.APP_OBJ)
            self.selection = value

        self.hide()
        self.on_dialog_ok(selection, self.mtypes)



    def on_add_new_app(self, new_app):
        if new_app is not None:
            name, icon, cl =  mime_operations.get_app_bio(new_app, ICON_SIZE)
            tree_iter = self.list_store.append([new_app, name, icon, cl])
            self.alt_view.get_selection().select_iter(tree_iter)

    def on_add_app_clicked(self, *args):
        if self.add_app_dialog is None:
            self.add_app_dialog = AddAppDialog(self.builder, self.dialog,\
                                               self.on_add_new_app)

        self.add_app_dialog.show()


class MainWidget:
    def __init__(self, builder, window):
        self.builder = builder
        self.window = window

        self.builder.add_from_file(GLADE_FILE)
        self.builder.connect_signals(self)

        self.root_widget = self.builder.get_object("root_widget")

        self.cat_view = CategoriesView(self.builder,
                                       self.on_category_changed)

        self.mime_view = mime_view_cat_mode.MimeViewCategories(self.builder,
                                                             self.on_mtypes_edit,
                                                             self.on_mtypes_reset)

        self.dialog = MimeSetDialog(self.builder,
                                    self.window,
                                    self.on_mtypes_edit_ok)

        self._init_buttons()

    def _init_buttons(self):
        # only show mimetypes that have an associated application
        hide_unknown_flag = self.builder.get_object("show_associated_only_button")
        hide_unknown_flag.connect("toggled", self.on_hide_unknown_flag_toggled)
        hide_unknown_flag.set_active(SHOW_ONLY_ASSOCIATED)


    def get_widget(self):
        return self.root_widget

    def on_hide_unknown_flag_toggled(self, flag_widget):
        hide_unknown = flag_widget.get_active()
        self.mime_view.filter_associated(show_all = not hide_unknown)

    def on_category_changed(self, category_id):
        self.mime_view.filter_category(category_id[0])

    def on_mtypes_edit_ok(self, app, mtypes):
        if app is not None:
            mime_operations.set_app_default(app, mtypes)
            self.mime_view.update_data(mtypes)


    def on_mtypes_edit(self, *args):
        selected_mime_types = self.mime_view.get_selection()

        self.dialog.show(selected_mime_types)

    def on_mtypes_reset(self, *args):
        selected_mime_types = self.mime_view.get_selection()

        mime_operations.reset_associations(selected_mime_types)

        self.mime_view.update_data(selected_mime_types)


