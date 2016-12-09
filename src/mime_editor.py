#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  7 15:11:32 2016

@author: pavel
"""
import os
DIR = os.path.dirname(os.path.realpath(__file__))

import sys
sys.path.append('./common')
sys.path.append('./app_mode')
sys.path.append('./cat_mode')

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import locale
locale.setlocale(locale.LC_ALL, '')
if os.path.isdir("./locale"):
    locale.bindtextdomain(APP, "./locale")
    locale.textdomain(APP)
from locale import gettext as _

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C

import mime_editor_app_mode
import mime_editor_cat_mode

APP = os.path.join(DIR, "python-mime-editor-gui")
GLADE_FILE = "ui_main_window.glade"

editor_modes = {  "by_apps" : mime_editor_app_mode.MainWidget,
                    "by_categories" : mime_editor_cat_mode.MainWidget }

class MainWindow:
    def __init__(self, mode):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file(GLADE_FILE)

        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self.on_close)

        self.viewport = self.builder.get_object("main_box")


        editor = editor_modes.get(mode)(self.builder, self.window)

        self.viewport.pack_start(editor.get_widget(), True, True, 0)


    def run(self):
        self.window.show()
        Gtk.main()

    def on_close(self, *args):
        Gtk.main_quit()


if __name__ == "__main__":
    #main(sys.argv)
    #window = MainWindow("by_categories")
    window = MainWindow("by_apps")
    window.run()
