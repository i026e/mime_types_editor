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
    
def get_app_from_cline(cline, name, terminal):
    """   cl - command line
          name - app name
          terminal - open in terminal """
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
    
def get_known_mtypes():
    return Gio.content_types_get_registered()
    
def get_apps_for_mtype(mime_type):
    return Gio.app_info_get_all_for_type(mime_type)

def set_app_default(app, m_types):    
    for m_type in m_types:
        try:
            app.set_as_default_for_type(m_type)
        except Exception as e:
            print(e)

def reset_association(m_type):
    try: 
        Gio.AppInfo.reset_type_associations(m_type)
    except Exception as e:
            print(e)        
            
def get_apps_for_mtypes(mime_types_list):
    apps = {}  
    for mtype in mime_types_list:
        for app in get_apps_for_mtype(mtype):
            #using id_ to eliminate duplicates
            id_ = app.get_commandline()#app.get_id()
            apps[id_] = app
    return list(apps.values())

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