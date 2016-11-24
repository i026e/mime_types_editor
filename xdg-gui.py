#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 06:50:25 2016

@author: pavel
"""
import os
import sys 

import threading

   
#import mime_types
#import xdg_operations 
import mime_operations


APP = 'xdg-gui'

import locale
from locale import gettext as _
locale.setlocale(locale.LC_ALL, '')
if os.path.isdir("./locale"):
    locale.bindtextdomain(APP, "./locale")
    locale.textdomain(APP)
    
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio
from gi.repository import GdkPixbuf

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C


GLADE_FILE = "ui.glade"
ICON_SIZE = 16
SHOW_ONLY_ASSOCIATED = True

# using indecies shoud speed up filtering
ALL_CATEGORY = "All"
ALL_CATEGORY_ID = 0

MIMETYPES_IDS = {"application" : 1,
                 "audio" : 2, 
                 "image" : 3,
                 "text"  : 4, 
                 "video" : 5, }
                 
CATEGORY_IDS = {  "Application" : 1,
                        "Audio" : 2,
                        "Image" : 3,
                        "Text"  : 4,
                        "Video" : 5,                        
                         }
                        
# name, icon
CATEGORY_ICONS = {"Application" : "application-x-executable",
                        "Audio" : "audio-x-generic",
                        "Image" : "image-x-generic",
                        "Text"  : "text-x-generic",
                        "Video" : "video-x-generic",                        
                        "All"   : "unknown"}

def get_category_id(mime_type):
    if mime_type is None: return ALL_CATEGORY_ID
    
    slash_ind = mime_type.find("/")
    
    if slash_ind <= 0: return ALL_CATEGORY_ID
    
    top_level = mime_type[:slash_ind]
    return MIMETYPES_IDS.get(top_level, ALL_CATEGORY_ID)
    
    
class ImageTextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, model_index_img, model_index_txt, *args, **kwargs):
        super(ImageTextColumn, self).__init__(column_name, *args, **kwargs)
        
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_text = Gtk.CellRendererText()
        
        self.pack_start(renderer_pixbuf, expand = False)
        self.add_attribute(renderer_pixbuf, "pixbuf", model_index_img)
        
        self.pack_start(renderer_text, expand = True)
        self.add_attribute(renderer_text, "text", model_index_txt)
        
class TextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, model_index_txt, *args, **kwargs):
        super(TextColumn, self).__init__(column_name, *args, **kwargs)        
        renderer_text = Gtk.CellRendererText()
        
        self.pack_start(renderer_text, expand = True)
        self.add_attribute(renderer_text, "text", model_index_txt)

class IconTextLabel(Gtk.Box):
    def __init__(self, icon_name, text, *args, **kwargs):
        super( IconTextLabel, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)
        
        icon = mime_operations.get_icon_by_name(icon_name, ICON_SIZE)
        label = Gtk.Label(text)
        
        self.pack_start(icon, True, True, 0)
        self.pack_start(label, True, True, 0)
        
    
class CategoriesView:
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
        
        column = ImageTextColumn(_("Categories"), self.CAT_IMG, self.CAT_NAME)
        self.categories_view.append_column(column)
        
        #register callback
        tree_selection = self.categories_view.get_selection()
        tree_selection.connect("changed", self.on_selection_changes)
        
    def _fill_list_store(self):
        categories = sorted((_(name), name ,id_) 
                            for name, id_ in CATEGORY_IDS.items())
        categories.append((_(ALL_CATEGORY), ALL_CATEGORY, 
                           ALL_CATEGORY_ID))

        
        for transl, name, id_ in categories:
            icon_name = CATEGORY_ICONS.get(name)            
            icon = mime_operations.get_icon_by_name(icon_name, ICON_SIZE)
            self.list_store.append([id_, transl, icon])
            
    def on_selection_changes(self, tree_selection):
        (model, pathlist) = tree_selection.get_selected_rows()
        cat_ids = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, self.CAT_ID)
            cat_ids.append(value)
        self.on_category_changed(cat_ids)
                      
class MimeTypesView:
    ID = 0
    MTYPE, MTYPE_IMG  = 1, 2
    APP,APP_IMG  = 3, 4
    
    def __init__(self, builder, on_items_edit, on_items_reset):
        """             
            on_items_edit : function to call when edit action required
            on_items_reset : function to call when reset action required                                    
        """
        
        self.mimetypes_view = builder.get_object("mimetypes_view")
        #callbacks
        self.mimetypes_view.connect("button-press-event", self.on_mouse_clicked)
        self.mimetypes_view.connect("key-press-event", self.on_key_pressed)
        
        self.on_items_edit = on_items_edit
        self.on_items_reset = on_items_reset
        
        self.current_category_id  = ALL_CATEGORY_ID
        self.hide_unassociated = False
        
        self._init_model()
        self._add_columns()
        
        self._init_context_menu(builder) 
        self._init_buttons(builder)
        
        self.set_data()
        
    def _init_model(self):
        """liststore -> filter -> sort -> view"""
        
        # category_id, mimetype, mimetype_img, app, app_img 
        self.list_store = Gtk.ListStore(int, str, GdkPixbuf.Pixbuf,
                                        str, GdkPixbuf.Pixbuf, )
        
        #filter
        self.cascade_filter = self.list_store.filter_new()
        self.cascade_filter.set_visible_func(self._cascade_filter_func)
        
        #sorting
        self.sorted = Gtk.TreeModelSort(self.cascade_filter)        
        self.mimetypes_view.set_model(self.sorted)
        
        #allow multiple selection
        self.mimetypes_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        
    def _add_columns(self):
         #add columns    
        column_type = ImageTextColumn(_("MimeType"), self.MTYPE_IMG, self.MTYPE)
        column_type.set_sort_column_id(self.MTYPE)        
        self.mimetypes_view.append_column(column_type)        
        
        column_program = ImageTextColumn(_("Program"), self.APP_IMG, self.APP)        
        column_program.set_sort_column_id(self.APP)
        self.mimetypes_view.append_column(column_program)
    
    def _init_context_menu(self, builder):
        self.context_menu = builder.get_object("mimeview_context_menu")
        revert_item = builder.get_object("menuitem_revert")
        edit_item = builder.get_object("menuitem_edit")
        
        revert_item.connect("activate", lambda *args : self.on_items_reset())
        edit_item.connect("activate",  lambda *args : self.on_items_edit())   
        
    def _init_buttons(self, builder):
        reset_button = builder.get_object("reset_button")
        edit_button = builder.get_object("edit_button")
        
        reset_button.connect("clicked", lambda *args : self.on_items_reset())
        edit_button.connect("clicked",  lambda *args : self.on_items_edit())   
        
                
    def set_data(self):      
        for m_type in mime_operations.get_known_mtypes():
            cat_id_ = get_category_id(m_type)
            m_type_img = mime_operations.get_mime_icon(m_type, ICON_SIZE)
            
            app = mime_operations.get_default_app(m_type)
            name, icon, *extra = mime_operations.get_app_bio(app, ICON_SIZE)
            
            self.list_store.append([cat_id_, m_type, m_type_img ,name, icon])
            
    def update_data(self, m_types_to_change):
        tree_iter = self.list_store.get_iter_first()
        
        while tree_iter:
            row_mtype = self.list_store.get_value(tree_iter, self.MTYPE)
            
            if row_mtype in m_types_to_change:
                app = mime_operations.get_default_app(row_mtype)
                name, icon, *extra = mime_operations.get_app_bio(app, ICON_SIZE)
                
                self.list_store.set_value(tree_iter, self.APP, name)
                self.list_store.set_value(tree_iter, self.APP_IMG, icon)                
                
            tree_iter = self.list_store.iter_next(tree_iter)
            
             
    def _cascade_filter_func(self, *args, **kwargs):
        return self._category_filter_func(*args, **kwargs) \
                and self._associated_filter_func(*args, **kwargs)        
            
    def _category_filter_func(self, model, iter, data):
        if self.current_category_id  == ALL_CATEGORY_ID: return True
        
        return model[iter][self.ID] == self.current_category_id
        
    def _associated_filter_func(self, model, iter, data):
        if not self.hide_unassociated: return True
                
        return (model[iter][self.APP] is not None) and \
               (len(model[iter][self.APP]) > 0)
    
    def filter_category(self, category_id = ALL_CATEGORY_ID):
        self.current_category_id = category_id
        self.cascade_filter.refilter()
        
    def filter_associated(self, hide_unassociated = False):        
        self.hide_unassociated = hide_unassociated        
        self.cascade_filter.refilter()
        
        
    def on_mouse_clicked(self, widget, event):
        if event.button == 3: #right button
            self.show_context_menu(event)     
            return True
        if event.type == Gdk.EventType._2BUTTON_PRESS: #double click
            self.on_items_edit()
            return True

    def on_key_pressed(self, widget, event):
        #do not reset selection
        keyname = Gdk.keyval_name(event.keyval)
        print(keyname, "pressed")
        
        if keyname in {"Return", "Enter", "space"}:
            self.on_items_edit()
            return True
        elif keyname in {"BackSpace", "Delete"}:
            self.on_items_reset()
            return True
            

    def show_context_menu(self, event):
        self.context_menu.popup( None, None, None, None, 
                                event.button, event.time)
        
    def get_selection(self):
        """return mime types from selected rows"""
        
        tree_selection = self.mimetypes_view.get_selection()
        (model, pathlist) = tree_selection.get_selected_rows()
        
        selected_mime_types = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, self.MTYPE)
            
            selected_mime_types.append(value)
            
        return selected_mime_types

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

            name = os.path.basename(self.cline_text)
            self.selected_app = mime_operations.get_app_from_cline(self.cline_text,
                                                                   name,
                                                                   False)
        
    def on_application_selected(self, widget, app):       
        self.selected_app = app
        
        name, icon, self.cline_text =  mime_operations.get_app_bio(app, ICON_SIZE)
        self.custom_entry.set_text(self.cline_text)
        
    def on_file_chooser(self, *args):
        f_dialog = Gtk.FileChooserDialog(_('Choose an application'),
                                       action = Gtk.FileChooserAction.OPEN, 
                                       buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                                  Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        f_dialog.set_current_folder('/usr/bin')
        f_dialog.set_transient_for(self.dialog)
        
        if f_dialog.run() == Gtk.ResponseType.ACCEPT:
            self.custom_entry.set_text(f_dialog.get_filename())

        f_dialog.destroy()
        
    def on_apply(self, *args):
        #“application-activated”
        self.on_add_dialog_apply(self.selected_app)
        self.hide()
    
              
class MimeSetDialog:
    APP_OBJ = 0
    APP_NAME = 1
    APP_ICON = 2
    APP_CL = 3
    
    
    def __init__(self, builder, parent_window, on_dialog_closed):
        self.builder = builder
        
        self.on_dialog_closed = on_dialog_closed        
        
        self.dialog = self.builder.get_object("mimetype_set_dialog")
        self.dialog.set_transient_for(parent_window)         
        self.dialog.connect("delete-event", self.hide)

        self.mtypes_dialog_label = builder.get_object("mtypes_dialog_label")
        
        self._init_buttons()
        self._init_view()
        
        
        #
        self.selection = None
        self.m_types = []

        
        
        self.add_app_dialog = None
        
        
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
        
        column_app = ImageTextColumn(_("Categories"), self.APP_ICON, self.APP_NAME)
        column_app.set_sort_column_id(self.APP_NAME)

        self.alt_view.append_column(column_app)
        
        column_cl = TextColumn(_("Command line"), self.APP_CL)
        column_cl.set_sort_column_id(self.APP_CL)

        self.alt_view.append_column(column_cl)
        
    def show(self, m_types):
        self.m_types = m_types
        self.set_data()
        self.indicate_default()        
        
        self.mtypes_dialog_label.set_text(" \n".join(self.m_types))
        
        self.selection = None
        
        self.dialog.run()
        
    def hide(self, *args):
        self.dialog.hide()        
        self.list_store.clear()
        
        self.on_dialog_closed(self.selection, self.m_types)
        
        return True #!!!
        
    def set_data(self):
        #if self.vbox is not None: return
        apps = mime_operations.get_apps_for_mtypes(self.m_types)        
            
        for app in apps:
            name, icon, cl =  mime_operations.get_app_bio(app, ICON_SIZE)
                       
            self.list_store.append([app, name, icon, cl])

    def indicate_default(self):
        if len(self.m_types) == 1:
            default_app = mime_operations.get_default_app(self.m_types[0])
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
                
        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, self.APP_OBJ)
            self.selection = value
            
        self.hide()
    
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
        
              
class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file(GLADE_FILE)
        self.builder.connect_signals(self)
        
        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self.on_close)
        
        
        self.cat_view = CategoriesView(self.builder,
                                       self.on_category_changed)
        
        self.mime_view = MimeTypesView(self.builder,                                     
                                       self.on_mtypes_edit,
                                       self.on_mtypes_reset)
        
        self.dialog = MimeSetDialog(self.builder,
                                    self.window,
                                    self.on_mtypes_edit_complete)
        
        # only show mimetypes that have associated application
        self.hide_unknown_flag = self.builder.get_object("show_associated_only_button")
        self.hide_unknown_flag.connect("toggled", self.on_hide_unknown_flag_toggled)
        self.hide_unknown_flag.set_active(SHOW_ONLY_ASSOCIATED)
      

    def run(self):        
        self.window.show()        
        Gtk.main()
        
    def on_close(self, *args):
        Gtk.main_quit()
               
    def on_hide_unknown_flag_toggled(self, flag_widget):
        hide_unknown = flag_widget.get_active()
        self.mime_view.filter_associated(hide_unknown)
        
    def on_category_changed(self, category_id):
        self.mime_view.filter_category(category_id[0])
        
    def on_mtypes_edit_complete(self, app, m_types):
        if app is not None:
            mime_operations.set_app_default(app, m_types)
            self.mime_view.update_data(m_types)
        
            
    def on_mtypes_edit(self):
        selected_mime_types = self.mime_view.get_selection()
                
        self.dialog.show(selected_mime_types)
    
    def on_mtypes_reset(self):
        selected_mime_types = self.mime_view.get_selection()
        
        for m_type in selected_mime_types:
            mime_operations.reset_association(m_type)
        
        self.mime_view.update_data(selected_mime_types)
        
        

    
if __name__ == "__main__":
    window = MainWindow()
    window.run()

