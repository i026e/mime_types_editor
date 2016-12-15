#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 18:26:27 2016

@author: pavel
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk
from gi.repository import GdkPixbuf

import os.path

from functools import lru_cache

def get_default_app(mime_type):
    return Gio.app_info_get_default_for_type(mime_type, False)
    
def get_app_from_cline(cline, name, terminal = False):
    """   cl - command line
          name - app name
          terminal - open in terminal """
          
    if cline is None or len(cline) == 0:
        return None
          
    if name is None or len(name) == 0:
        name = os.path.basename(cline)
    flag = Gio.AppInfoCreateFlags.NEEDS_TERMINAL if terminal \
                else Gio.AppInfoCreateFlags.NONE 
    return Gio.AppInfo.create_from_commandline(cline, name, flag)    

@lru_cache(maxsize=256)   
def get_app_bio(app, icon_size):    
    name = ""
    icon = None
    cl = ""
    
    if app is not None:
        name = app.get_name()
        icon = get_icon_by_app(app, icon_size)
        cl = app.get_commandline()
        
    return name, icon, cl
    
    
@lru_cache(maxsize=256)
def get_mime_bio(mime_type, icon_size):
    description = ""
    icon = None
    
    try:
        description = Gio.content_type_get_description(mime_type)
        icon = get_mime_icon(mime_type, icon_size)
    except Exception as e:
        print(e)   
    
    return description, icon
           
    
def get_known_mtypes():
    return Gio.content_types_get_registered()
    
def get_mtypes_for_app(app) :
    if app is None : return []
    mtypes = set(app.get_supported_types()) 
    #does not take in consideration associations added with g_app_info_add_supports_type()
    
    
    for mtype in get_known_mtypes():
        for a in get_apps_for_mtype(mtype):
            if app.equal(a):
                mtypes.add(mtype)
                break
    
    return sorted(list(mtypes))
    
def get_apps_for_mtype(mime_type):
    return Gio.app_info_get_all_for_type(mime_type)
    
def get_apps_for_mtypes(mime_types_list):
    apps = {}  
    for mtype in mime_types_list:
        for app in get_apps_for_mtype(mtype):
            #using id_ to eliminate duplicates
            id_ = app.get_commandline()#app.get_id()
            apps[id_] = app
    return list(apps.values())    
    
def is_app_associated(app, mtype):
    associated_app_ids = [ap.get_id() for ap in get_apps_for_mtype(mtype)]
    return app.get_id() in associated_app_ids
    
def is_app_default(app, mtype):
    try:
        default = get_default_app(mtype)
        return app.equal(default)
    except Exception as e:
        print(e)
        return False
    
def set_app_default(app, mtypes):    
    for mtype in mtypes:
        try:
            app.set_as_default_for_type(mtype)
        except Exception as e:
            print(e)

def reset_associations(mtypes):
    for mtype in mtypes:
        try: 
            Gio.AppInfo.reset_type_associations(mtype)
        except Exception as e:
                print(e)
                
def add_associations(app, mtypes):
    for mtype in mtypes:
        try: 
            app.add_supports_type(mtype)
        except Exception as e:
                print(e)                
            
def remove_associations(app, mtypes):
    for mtype in mtypes:
        try: 
            app.remove_supports_type(mtype)
        except Exception as e:
                print(e)    
            

    
def get_all_apps():    
    return Gio.app_info_get_all()

@lru_cache(maxsize=256)   
def get_icon_by_name(icon_name, size): 
    icon = None
    if icon_name is not None:
        try:
            icon = Gtk.IconTheme.get_default().load_icon(icon_name, size, 0);    
        except:
            try:
                icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_name, 
                                                               size, size, True)
            except Exception as e:
                print(icon_name, e)
                
    return icon    
    
@lru_cache(maxsize=256)    
def get_icon_by_app(app, size):
    #ubuntu-tweak
    
    icon = None
    try:
        gicon = app.get_icon()        

        if gicon and isinstance(gicon, Gio.ThemedIcon):
            names = gicon.get_names()
            names_list = []

            for name in names:
                names_list.append(os.path.splitext(name)[0])


            theme = Gtk.IconTheme.get_default()                        
            iconinfo = Gtk.IconTheme.choose_icon(theme, names_list, size, 
                                                 Gtk.IconLookupFlags.USE_BUILTIN)
            if iconinfo:
                icon = iconinfo.load_icon()
            
        elif gicon and isinstance(gicon, Gio.FileIcon):
            icon_path = app.get_icon().get_file().get_path()
            
            if icon_path:
                icon = get_icon_by_name(icon_path, size)
                
    except Exception as e:
        print(app, e)
        
    return icon
 
@lru_cache(maxsize=256)     
def get_mime_icon(mtype, size):
    icon = None
    
    try:
        gicon = Gio.content_type_get_icon(mtype)
        
        theme = Gtk.IconTheme.get_default()
        iconinfo = Gtk.IconTheme.choose_icon(theme, gicon.get_names(), size, 
                                         Gtk.IconLookupFlags.USE_BUILTIN)
        if iconinfo:            
            icon = iconinfo.load_icon()
            
            if icon and icon.get_width() != size:
                icon = icon.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)

    except Exception as e:
        print(e)

    return icon
 
