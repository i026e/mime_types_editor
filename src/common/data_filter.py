#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 25 07:18:57 2016

@author: pavel
"""

import mime_categories
import re

class DataFilter:
    def __init__(self, enabled = True):
        self.enabled = enabled
    def process_row(self, model, iter_, data):
        return not self.enabled
    def set_params(self, **kwargs):
        for param_name, param_value in kwargs.items():
            print("filtering", param_name, param_value)
            if param_name in self.__dict__:
                self.__dict__[param_name] = param_value

class GeneralFilter(DataFilter):
    def __init__(self, enabled, column, value_condition_fn):
        self.enabled = enabled
        self.column = column
        self.value_condition_fn = value_condition_fn
    def process_row(self, model, iter_, data):
        if not self.enabled: return True
        value = model.get_value(iter_, self.column)
        return self.value_condition_fn(value)

class RegexFilter(DataFilter):
    def __init__(self, matchstring):
        self._new_regex(matchstring)

    def _new_regex(self, matchstring):
        self.matchstring = matchstring
        if matchstring == "":
            self.matchregex = ".*"
        else:
            self.matchregex = ".*" + matchstring + ".*"
        self.pattern = re.compile(self.matchregex, re.IGNORECASE)
        #print("Setting RegexFilter to:",self.matchregex)

    def process_row(self, model, iter_, data):
        if self.matchstring != data:
            self._new_regex(data)
        # columns from MimeView class in mime_view.py
        instring=model.get_value(iter_,2)
        in_column2 = self.pattern.match(instring)
        instring=model.get_value(iter_,0)
        in_column0 = self.pattern.match(instring)
        #print("ROW ",'"' + instring + '"', " test against regex", self.matchstring, "is", in_column2, "data=",data)
        return in_column2 != None or in_column0 != None

class CategoryFilter(DataFilter):
    def __init__(self, category_column, current_category_id):
        self.category_id_column = category_column
        self.current_category_id = current_category_id

    def process_row(self, model, iter_, data):
        if self.current_category_id == mime_categories.ANY_CATEGORY_ID:
            return True

        return model.get_value(iter_, self.category_id_column) == self.current_category_id
