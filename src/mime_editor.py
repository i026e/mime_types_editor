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

APP = os.path.join(DIR, "mime-editor-gui")
GLADE_FILE = "ui_main_window.glade"

editor_modes = {  "app_mode" : mime_editor_app_mode.MainWidget,
                  "cat_mode" : mime_editor_cat_mode.MainWidget }

class MainWindow:
    def __init__(self, mode):
        self.current_mode = mode

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file(GLADE_FILE)

        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self.on_close)

        self.viewport = self.builder.get_object("main_box")


        editor = editor_modes.get(mode)(self.builder, self.window)

        self.viewport.pack_start(editor.get_widget(), True, True, 0)

        self._init_menu()

    def _init_menu(self):
        quit_menuitem = self.builder.get_object("quit_menuitem")
        quit_menuitem.connect("activate", self.on_close)

        #change mode
        cat_mode_menuitem = self.builder.get_object("cat_mode_menuitem")
        app_mode_menuitem = self.builder.get_object("app_mode_menuitem")
        if self.current_mode == "cat_mode":
            cat_mode_menuitem.set_active(True)
        elif self.current_mode == "app_mode":
            app_mode_menuitem.set_active(True)
        cat_mode_menuitem.connect("activate", self.switch_mode, "cat_mode")
        app_mode_menuitem.connect("activate", self.switch_mode, "app_mode")

    def run(self):
        self.window.show()
        Gtk.main()

    def on_close(self, *args):
        Gtk.main_quit()

    def switch_mode(self, widget, new_mode):
        if new_mode != self.current_mode:
            os.execl(sys.executable, sys.executable, sys.argv[0], new_mode)


if __name__ == "__main__":
    mode = "cat_mode"
    if len(sys.argv) > 1 and sys.argv[1] in editor_modes:
        mode = sys.argv[1]

    window = MainWindow(mode)
    window.run()
