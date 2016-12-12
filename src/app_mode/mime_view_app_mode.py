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
import mime_operations, mime_categories
import mime_view
import data_filter


from locale import gettext as _



class MimeViewApps(mime_view.MimeView):
    UI_VIEW_ID = "treeview_mime_associations"
    UI_CONTEXT_MENU_ID = "mime_view_context_menu"

    #model columns
    MIME_TYPE = 0
    MIME_CATEGORY = 1
    MIME_DESC = 2
    MIME_ICON = 3
    MIME_ASSOCIATED_WITH_APP = 4
    MIME_SELECTED = 5
    MIME_DEFAULT_SELECTED = 6
    MIME_CHANGEABLE = 7 # forbidden to take mark of
    MIME_DELETED = 8
    MIME_COLOR = 9

    CELL_COLOR_NORMAL = "white"
    CELL_COLOR_DELETED = "red"

    LIST_STORE_COLUMN_TYPES = [str, int, str, GdkPixbuf.Pixbuf,
                               bool, bool, bool,
                               bool, bool, str]

    # mtype, mtype_description, mtype_icon,
    # mtype_selected. mtype_selected_by_default,
    # mtype_possible_to change_selection
    # mtype_deleted, background_color


    def __init__(self, *args, **kwargs):
        super(MimeViewApps, self).__init__(*args, **kwargs)

        self.list_store_modified = self.set_consistence
        self.menuitem_delete = self.builder.get_object("delete_menuitem")

    def _init_mappings(self):
        super(MimeViewApps, self)._init_mappings()
        self.context_menu_items.update({"mark_menuitem": lambda *param : self.mark_selected(mark = True),
                                   "unmark_menuitem": lambda *param : self.mark_selected(mark = False),
                                   "reset_menuitem": lambda *param : (self.reset_mark_selected(),
                                                                       self.undelete_selected()),
                                   "delete_menuitem": lambda *param : self.delete_selected()
                                   })

        invert_selection = lambda *param : self.mark_selected(invert = True)
        self.keyboard_keys_actions.update({"Return" : invert_selection,
                                      "Enter" : invert_selection,
                                      "space" : invert_selection,
                                      "BackSpace" : lambda *param : self.reset_mark_selected(),
                                      "Delete" : lambda *param : self.delete_selected()
                                      })

    def _init_filters(self):
        super(MimeViewApps, self)._init_filters()

        associated_filter = data_filter.GeneralFilter(True, self.MIME_ASSOCIATED_WITH_APP,
                                          lambda is_assosiated : is_assosiated)

        self._add_filter_to_cascade("associated_filter", associated_filter)


    def _init_columns(self, *args, **kwargs):
        self._add_flag_column()
        self._add_filetype_column()
        self._add_name_column()

        #colors
        self.flag_column.set_attribute("cell-background", self.MIME_COLOR)
        self.desc_column.set_attribute("cell-background", self.MIME_COLOR)
        self.name_column.set_attribute("cell-background", self.MIME_COLOR)

    def _add_flag_column(self):
        self.flag_column = gtk_common.FlagColumn("" ,self.MIME_SELECTED,
                                 self.on_flag_toggled, self.on_mark_all_clicked)
        self.flag_column.set_attribute("activatable", self.MIME_CHANGEABLE)
        self.mtypes_view.append_column(self.flag_column)

    def _add_name_column(self):
        self.name_column = gtk_common.TextColumn(_("Mime Type"), self.MIME_TYPE)
        self.name_column.set_sort_column_id(self.MIME_TYPE)
        self.mtypes_view.append_column(self.name_column)

    def set_data(self, app):
        self.list_store.clear()
        mtypes = self._get_initial_data(app)
        self._add_mtypes(mtypes, app, initialization = True)

    def _add_mtypes(self, mtypes, app, initialization = False):
        super(MimeViewApps, self)._add_mtypes(mtypes, app)
        self.set_consistence(initial_mode = initialization)

    #def _get_initial_data(self, app):
    #    return mime_operations.get_mtypes_for_app(app)

    def _get_model_data_row(self, mtype, app):
        mtype, category, descr, icon = super(MimeViewApps, self)._get_model_data_row(mtype)
        associated = mime_operations.is_app_associated(app, mtype)

        selected = default = associated and mime_operations.is_app_default(app, mtype)
        changeable = not selected

        deleted = False
        cell_color = self.CELL_COLOR_NORMAL
        # mtype, mtype_description, mtype_icon,
        # mtype_selected. mtype_selected_by_default,
        # mtype_possible_to change_selection
        # mtype_deleted, background_color

        return [mtype, category, descr, icon,
                associated,
                selected, default, changeable,
                deleted, cell_color]


    def delete_selected(self):
        self.set_value_to_selected(self.MIME_DELETED, value = True)
        self.set_value_to_selected(self.MIME_COLOR, value = self.CELL_COLOR_DELETED)


    def undelete_selected(self):
        self.set_value_to_selected(self.MIME_DELETED, value = False)
        self.set_value_to_selected(self.MIME_COLOR, value = self.CELL_COLOR_NORMAL)

    def changeable(self, model, iter_):
        return model.get_value(iter_, self.MIME_CHANGEABLE)

    def get_swapped_mark(self, model, iter_):
        return not model.get_value(iter_, self.MIME_SELECTED)

    def get_default_mark(self, model, iter_):
        return model.get_value(iter_, self.MIME_DEFAULT_SELECTED)

    def reset_mark_all(self):
        self.set_value_to_all(self.MIME_SELECTED, get_value_func = self.get_default_mark)
        self.set_consistence()

    def reset_mark_visible(self):
        set_value_to_visible(self.MIME_SELECTED, get_value_func = self.get_default_mark)
        self.set_consistence()

    def reset_mark_selected(self):
        self.set_value_to_selected(self.MIME_SELECTED,
                                   get_value_func = self.get_default_mark)
        self.set_consistence()

    def mark_all(self, mark = True):
        self.set_value_to_all(self.MIME_SELECTED, value = mark,
                              conditions_func = self.changeable)
        self.set_consistence()

    def mark_visible(self, mark = True):
        self.set_value_to_visible(self.MIME_SELECTED, value = mark,
                              conditions_func = self.changeable)
        self.set_consistence()

    def mark_selected(self, invert = False, mark = True):
        """for inversion mark parameter will be ignored"""
        if invert:
            self.set_value_to_selected(self.MIME_SELECTED,
                                   get_value_func = self.get_swapped_mark,
                                   conditions_func = self.changeable)
        else:
            self.set_value_to_selected(self.MIME_SELECTED,
                                   value = mark,
                                   conditions_func = self.changeable)

        self.set_consistence()

    def swap_mark_by_path(self, path):
        iter_ = self.list_store.get_iter(self.get_store_path(path))
        self.set_value_if_cond(self.list_store, iter_,
                               self.MIME_SELECTED,
                               get_value_func = self.get_swapped_mark,
                               conditions_func = self.changeable)
        self.set_consistence()

    def get_changed_mtypes(self):
        to_delete = []
        to_set = []
        to_reset = []

        tree_iter = self.list_store.get_iter_first()
        while tree_iter:
            mtype = self.list_store.get_value(tree_iter, self.MIME_TYPE)

            delete = self.list_store.get_value(tree_iter, self.MIME_DELETED)
            if delete:
                to_delete.append(mtype)
            else:
                default_selected = self.list_store.get_value(tree_iter, self.MIME_DEFAULT_SELECTED)

                selected = self.list_store.get_value(tree_iter, self.MIME_SELECTED)

                if (selected) and (not default_selected):
                    to_set.append(mtype)
                elif (not selected) and (default_selected):
                    to_reset.append(mtype)

            tree_iter = self.list_store.iter_next(tree_iter)
        return to_delete, to_set, to_reset


    def on_flag_toggled(self, renderer, str_path, *data):
        self.swap_mark_by_path(Gtk.TreePath.new_from_string(str_path))


    def on_mark_all_clicked(self, reset, mark):
        """ If reset : default value would be restored
            otherwise : mark would be assigned to each row
        """
        if reset:
            self.reset_mark_visible()
        else:
            self.mark_visible(mark)

    def on_double_click(self, widget, event):
        self.mark_selected(invert = True) #invert mark

    def set_consistence(self, initial_mode = False):
        """check if all checkboxes are marked
        and set checkbox in column title

        if initial_mode, also degeneracy mode
        (only checked/unchecked states without inconsistency)
        for checkbox in column title

        """
        first_mark = None
        consistent = True

        for (model, iter_) in self.iterate_visible():
            if first_mark is None:
                first_mark = model.get_value(iter_, self.MIME_SELECTED)
            elif first_mark != model.get_value(iter_, self.MIME_SELECTED):
                consistent = False
                break

        if first_mark is None: #no records
            self.flag_column.set_flag_inactive()

        elif consistent: #consisten records
            self.flag_column.set_flag_active(first_mark)

            if initial_mode:
                self.flag_column.set_flag_degenerate(True)
        else:
            self.flag_column.set_flag_inconsistent()

            if initial_mode:
                self.flag_column.set_flag_degenerate(False)

    def filter_associated(self, show_all = False):
        self.set_filter_params("associated_filter",
                               enabled = not show_all)
        self.menuitem_delete.set_sensitive(not show_all)

