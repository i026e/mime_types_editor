#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 25 07:18:57 2016

@author: pavel
"""

import mime_categories

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



class CategoryFilter(DataFilter):
    def __init__(self, category_column, current_category_id):
        self.category_id_column = category_column
        self.current_category_id = current_category_id

    def process_row(self, model, iter_, data):
        if self.current_category_id == mime_categories.ANY_CATEGORY_ID:
            return True

        return model.get_value(iter_, self.category_id_column) == self.current_category_id