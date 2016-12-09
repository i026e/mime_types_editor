#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 14:51:39 2016

@author: pavel
"""

ANY_CATEGORY = "any"
ANY_CATEGORY_ID = 0 
ANY_CATEGORY_NAME = "All" 
ANY_CATEGORY_ICON = "unknown"

CATEGORY_IDS = {"application" : 1,
                 "audio" : 2, 
                 "image" : 3,
                 "text"  : 4, 
                 "video" : 5, }

CATEGORY_NAMES = {  "application" : "Application" ,
                    "audio" : "Audio",
                    "image" : "Image",
                    "text"  : "Text",
                    "video" : "Video"}  
                    
# name, icon
CATEGORY_ICONS = {"application" : "application-x-executable",
                        "audio" : "audio-x-generic",
                        "image" : "image-x-generic",
                        "text"  : "text-x-generic",
                        "video" : "video-x-generic"}


def get_category_id(mime_type):
    if mime_type is None: return ANY_CATEGORY_ID
    
    slash_ind = mime_type.find("/")
    
    if slash_ind <= 0: return ANY_CATEGORY_ID
    
    top_level = mime_type[:slash_ind]
    return CATEGORY_IDS.get(top_level, ANY_CATEGORY_ID)

def get_category_name(cat):
    return CATEGORY_NAMES.get(cat, ANY_CATEGORY_NAME)
    
def get_known_categories():
    """ list of (category, category name, id) """
    return [(cat , get_category_name(cat), id_) for cat, id_ 
                                                in  CATEGORY_IDS.items()]


def get_icon_name(cat) :
    return CATEGORY_ICONS.get(cat, ANY_CATEGORY_ICON)   