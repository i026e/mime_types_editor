#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 25 07:54:51 2016

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
import mime_view_app_mode

import gtk_common
from gtk_common import browse_for_file
from gtk_common import ICON_SIZE



print(os.path.dirname(os.path.realpath(__file__)))
GLADE_FILE = os.path.join(DIR,"./ui_app_mode.glade")


class AppCard:
    def __init__(self, builder):
        self.builder = builder

        self.app_icon_view = self.builder.get_object("app_icon_view")
        self.app_name_label = self.builder.get_object("app_name_label")
        self.app_command_label = self.builder.get_object("app_command_label")

    def update(self, app):
        if app is not None:
            name, icon, cl = mime_operations.get_app_bio(app, ICON_SIZE)

            self.app_icon_view.set_from_pixbuf(icon)
            self.app_name_label.set_text(name)
            self.app_command_label.set_text(cl)


class AppsView:
    APP = 0
    APP_NAME = 1
    APP_IMG = 2
    APP_VISIBLE = 3
    APP_SUPPORT_FILES = 4
    def __init__(self, builder, on_app_changed):
        self.builder = builder
        self.on_app_changed = on_app_changed

        self.apps_view = self.builder.get_object("treeview_applications")

        self._init_model()
        self._add_columns()
        self._set_data()

        #register callback
        tree_selection = self.apps_view.get_selection()
        tree_selection.connect("changed", self.on_selection_changes)



    def _add_columns(self):
        column = gtk_common.ImageTextColumn(_("Application"), self.APP_IMG, self.APP_NAME)
        column.set_sort_column_id(self.APP_NAME)
        self.apps_view.append_column(column)

    def _init_model(self):
        """liststore -> filter -> sort -> view"""

        # app, name, icon, visible, support files,
        self.list_store = Gtk.ListStore(Gio.AppInfo, str ,GdkPixbuf.Pixbuf, bool, bool)

        #filter
        self.cascade_filter = self.list_store.filter_new()
        self.cascade_filter.set_visible_func(self._cascade_filter_func)
        self.show_invisible = False
        self.show_without_file_support = False

        #sorting
        self.sorted = Gtk.TreeModelSort(self.cascade_filter)
        self.apps_view.set_model(self.sorted)



    def _set_data(self):
        for app in mime_operations.get_all_apps():
            name, icon, cl = mime_operations.get_app_bio(app, ICON_SIZE)

            visible = app.should_show()
            f_support = app.supports_files() or app.supports_uris()

            self.list_store.append([app, name, icon, visible, f_support])

    def _cascade_filter_func(self, *args, **kwargs):
        return self._visible_only_filter_func(*args, **kwargs) and \
                self._with_file_support_only_filter_func(*args, **kwargs)

    def _visible_only_filter_func(self, model, iter, data):
        return self.show_invisible or model[iter][self.APP_VISIBLE]

    def _with_file_support_only_filter_func(self, model, iter, data):
        return self.show_without_file_support or model[iter][self.APP_SUPPORT_FILES]

    def filter_visible(self, show_invisible = False):
        self.show_invisible = show_invisible
        self.cascade_filter.refilter()

    def filter_without_file_support(self, show_without_file_support = False):
        self.show_without_file_support = show_without_file_support
        self.cascade_filter.refilter()

    def on_selection_changes(self, tree_selection):
        (model, pathlist) = tree_selection.get_selected_rows()
        app = None

        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, self.APP)
            app = value

        self.on_app_changed(app)

    def add_custom_app(self, app):
        if app is not None:
            name, icon, cl = mime_operations.get_app_bio(app, ICON_SIZE)
            iter_ = self.list_store.append([app, name, icon, True, True])


            path = self.list_store.get_path(iter_)
            self.apps_view.set_cursor(path)


class AddMTypeDialog:
    def __init__(self, builder, parent_window, on_dialog_ok):
        self.builder = builder
        self.on_dialog_ok = on_dialog_ok

        self.dialog = self.builder.get_object("add_mime_type_dialog")
        self.dialog.set_transient_for(parent_window)
        self.dialog.connect("delete-event", self.hide)

        self._init_buttons()

    def _init_buttons(self):
        self.ok_button = self.builder.get_object("add_mtype_ok_button")
        self.cancel_button = self.builder.get_object("add_mtype_cancel_button")

        self.ok_button.connect("clicked", self.on_ok_button_clicked)
        self.cancel_button.connect("clicked", self.hide)

    def hide(self, *args):
        self.dialog.hide()
        return True #!!!

    def show(self, app):
        self.dialog.run()

    def on_ok_button_clicked(self, *args):
        text_box = self.builder.get_object("new_mtype_entry")
        reg_button = self.builder.get_object("register_mtype_button")
        def_button = self.builder.get_object("set_default_mtype_button")
        
        mtype = text_box.get_text()        
        set_registered = reg_button.get_active()
        set_default = def_button.get_active()

        self.on_dialog_ok(mtype, set_registered, set_default)
        self.hide()

class AddAppDialog:
    def __init__(self, builder, parent_window, on_dialog_ok):
        self.builder = builder
        self.on_dialog_ok = on_dialog_ok

        self.dialog = self.builder.get_object("add_app_dialog")
        self.dialog.set_transient_for(parent_window)
        self.dialog.connect("delete-event", self.hide)

        self._init_buttons()

        self.name_field = self.builder.get_object("add_app_name_field")
        self.command_field = self.builder.get_object("add_app_command_field")

    def _init_buttons(self):
        self.ok_button = self.builder.get_object("add_app_ok_button")
        self.cancel_button = self.builder.get_object("add_app_cancel_button")
        self.browse_button = self.builder.get_object("app_browse_button")

        self.ok_button.connect("clicked", self.on_ok_button_clicked)
        self.cancel_button.connect("clicked", self.hide)
        self.browse_button.connect("clicked", self.on_browse_button_clicked)

    def hide(self, *args):
        self.dialog.hide()

        return True #!!!

    def show(self):
        #self.set_data()
        #self.indicate_default()

        #self.mtypes_dialog_label.set_text(" \n".join(self.mtypes))

        self.selection = None

        self.dialog.run()

    def on_ok_button_clicked(self, *args):
        name = self.name_field.get_text()
        command_line = self.command_field.get_text()
        app = mime_operations.get_app_from_cline(command_line, name)

        self.on_dialog_ok(app)
        self.hide()

    def on_browse_button_clicked(self, *args):
        browse_for_file(_('Choose an application'),
                        '/usr/bin',
                        self.dialog,
                        self.command_field.set_text)

class CategoriesBox(gtk_common.CategoriesWidget):
    DEFAULT_SELECTION = -1

    def __init__(self, builder, on_category_changed):
        super(CategoriesBox, self).__init__(builder, "categories_combobox",
                                                        on_category_changed)
        self.set_active(self.DEFAULT_SELECTION)

    def _init_widget(self):
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_text = Gtk.CellRendererText()

        self.widget.pack_start(renderer_pixbuf, expand = False)
        self.widget.add_attribute(renderer_pixbuf, "pixbuf", self.CAT_IMG)

        self.widget.pack_start(renderer_text, expand = True)
        self.widget.add_attribute(renderer_text, "text", self.CAT_NAME)

        self.widget.connect("changed", self.on_combobox_changed)

    def on_combobox_changed(self, widget):
        iter_ = widget.get_active_iter()
        value = self.list_store.get_value(iter_, self.CAT_ID)
        self.on_category_changed(value)

    def set_active(self, index):
        iter_ = self.list_store[index].iter
        self.widget.set_active_iter(iter_)

    def disable(self):
        self.widget.set_sensitive(False)

    def enable(self) :
        self.widget.set_sensitive(True)



class MainWidget:
    def __init__(self, builder, window):
        self.builder = builder
        self.window = window

        self.builder.add_from_file(GLADE_FILE)
        self.builder.connect_signals(self)

        self.root_widget = self.builder.get_object("root_widget")

        self.apps_view = AppsView(self.builder, self.on_app_selected)
        self.app_card = AppCard(self.builder)
        self.mimes_view = mime_view_app_mode.MimeViewApps(self.builder)
        self.categories_box = CategoriesBox(self.builder, self.on_category_changed)

        self.add_mtype_dialog = None
        self.add_app_dialog = None

        self._init_buttons()

        self.current_app = None

    def _init_buttons(self):
        visible_apps_only  = self.builder.get_object("visible_apps_only")
        visible_apps_only.connect("toggled", self.on_show_visible_toggled)

        apps_with_file_support_only = self.builder.get_object("apps_with_file_support_only")
        apps_with_file_support_only.connect("toggled", self.on_apps_with_file_support_toggled)

        show_only_registered_radiobutton = self.builder.get_object("show_only_registered_radiobutton")
        show_only_registered_radiobutton.connect("toggled",
                                                 self.on_show_only_registered_radiobutton_clicked)


        show_all_radiobutton = self.builder.get_object("show_all_radiobutton")
        show_all_radiobutton.connect("toggled",
                                     self.on_show_all_radiobutton_clicked)

        revert_button = self.builder.get_object("revert_button")
        revert_button.connect("clicked", self.on_revert_button_clicked)

        apply_button = self.builder.get_object("apply_button")
        apply_button.connect("clicked", self.on_apply_button_clicked)

        add_mtype_button = self.builder.get_object("add_mtype_button")
        add_mtype_button.connect("clicked", self.on_add_mtype_button_clicked)

        add_app_button = self.builder.get_object("add_app_button")
        add_app_button.connect("clicked", self.on_add_app_button_clicked)

    def get_widget(self):
        return self.root_widget

    def on_app_selected(self, app):
        self.current_app = app

        self.app_card.update(self.current_app)
        self.mimes_view.set_data(self.current_app)

    def on_show_visible_toggled(self, flag_widget):
        show_visible_only = flag_widget.get_active()
        self.apps_view.filter_visible(not show_visible_only)

    def on_apps_with_file_support_toggled(self, flag_widget):
        show_with_file_support_only = flag_widget.get_active()
        self.apps_view.filter_without_file_support(not show_with_file_support_only)

    def on_revert_button_clicked(self, *args):
        self.mimes_view.set_data(self.current_app)

    def on_apply_button_clicked(self, *args):
        to_delete, to_set, to_reset = self.mimes_view.get_changed_mtypes()

        print("deleting", to_delete)
        mime_operations.remove_associations(self.current_app, to_delete)
        print("setting default", to_set)
        mime_operations.set_app_default(self.current_app, to_set)
        print("resetting default", to_reset)
        mime_operations.reset_associations(to_reset)

        self.mimes_view.set_data(self.current_app)

    def on_add_mtype_button_clicked(self, *args):
        if self.add_mtype_dialog is None:
            self.add_mtype_dialog = AddMTypeDialog(self.builder,
                                                   self.window, self.on_add_mtype_ok)
        self.add_mtype_dialog.show(self.current_app)

    def on_add_app_button_clicked(self, *args):
        if self.add_app_dialog is None:
            self.add_app_dialog = AddAppDialog(self.builder,
                                                   self.window,
                                                   self.apps_view.add_custom_app)
        self.add_app_dialog.show()

    def on_show_only_registered_radiobutton_clicked(self, *args):
        self.mimes_view.filter_associated(show_all = False)
        self.categories_box.disable()
        self.categories_box.set_active(self.categories_box.DEFAULT_SELECTION)

    def on_show_all_radiobutton_clicked(self, *args):
        self.mimes_view.filter_associated(show_all = True)
        self.categories_box.enable()

    def on_category_changed(self, category):
        self.mimes_view.filter_category(category)
    
    def on_add_mtype_ok(self, mtype, set_registered, set_default):
        if set_registered:
            mime_operations.add_associations(self.current_app, [mtype])
            
        if set_default:
            mime_operations.set_app_default(self.current_app, [mtype])
            
        self.on_app_selected(self.current_app)


