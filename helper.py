#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 03:12:17 2022

@author: rugvedm
"""

# pylint: disable=too-many-instance-attributes, too-few-public-methods
# pylint: disable=too-many-ancestors, wrong-import-position

if __name__ == "__main__":
    print("Please run paint.py")

from pathlib import Path

from tkinter import Toplevel, Canvas, Button as TkButton#, PhotoImage
from tkinter.ttk import Frame, Label#, Notebook, Entry, Button, Style
from tkinter.colorchooser import askcolor

FILE_TYPES = (('PNG', '*.png'),
              ('JPEG', '*.jpeg'),
              ('GIF', '*.gif'),
              ('WEBP', '*.webp'),
              ('TIFF', '*.tiff'),
              ('EPS', '*.eps'))

CONFIG = Path("./paint_xd_config")
CONF_PKL = CONFIG / "config.pkl"

class MainConfig:
    def __init__(self):
        self.tabs = {}
        self.font = None
        self.poly_hint = True
        self.use_icons = False

class TabConfig:
    def __init__(self, tab=None):
        if tab:
            self.name = tab.name
            self.path = tab.path

            self.default_color = tab.default_color
            self.default_eraser = tab.default_eraser
            self.color = tab.color
            self.eraser_on = tab.eraser_on
            self.active_button = tab.active_button["text"] \
                if tab.active_button else None
            self.size = tab.size

            # Make menu option to change it
            # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_line.html
            self.capstyle = tab.capstyle

        else:
            self.name = None
            self.path = None

            self.default_color = 'black'
            self.default_eraser = 'white'
            self.color = self.default_color
            self.eraser_on = False
            self.active_button = None
            self.size = 1

            self.capstyle = 'butt'

class ClosableTabFrame(Frame, TabConfig):
    def __init__(self, root, tab):
        Frame.__init__(self, master=root.tabs_control)
        if type(tab) == str:
            TabConfig.__init__(self)
            self.name = tab
        elif type(tab) == TabConfig:
            TabConfig.__init__(self, tab)
        else:
            raise TypeError

        self.hidden = False
        self.root = root

        self.canvas = Canvas(self, bg='white')
        self.canvas.pack(expand=True, fill="both")

        self.history = []

    def activate_button(self, some_button, eraser_mode=False):
        if self.active_button:
            self.active_button.config(relief='raised')
        if some_button["text"] in ("Line", "Polygon"):
            self.canvas.unbind('<B1-Motion>')
        else:
            self.canvas.bind('<B1-Motion>', self.root.paint)
        some_button.config(relief='sunken')
        self.active_button = some_button
        self.eraser_on = eraser_mode
        self.root.use_cursor_icons()

class DefaultColorPopup(Toplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grab_set()

        self.title("Default Colors")
        self.master = master

        self.lbl_cur_def = Label(self, text="Current default color:")
        self.lbl_cur_def.grid(row=0, column=0)
        self.lbl_cur_def_clr = Label(self, bg=master.default_color,
                                     activebackground=master.default_color)
        self.lbl_cur_def_clr.grid(row=0, column=1)

        self.lbl_cur_ers = Label(self, text="Current eraser color:")
        self.lbl_cur_ers.grid(row=1, column=0)

        self.lbl_cur_ers_clr = Label(self, bg=master.default_eraser,
                                     activebackground=master.default_eraser)
        self.lbl_cur_ers_clr.grid(row=1, column=1)

        self.lbl_new_def = Label(self, text="Current default color:")
        self.lbl_new_def.grid(row=2, column=0)
        self.btn_new_def_clr = TkButton(self, text="Choose default color",
                                      command=self.update_default_color)
        self.btn_new_def_clr.grid(row=2, column=1)
        self.btn_def_def_clr = TkButton(self, bg="black",
                                      activebackground="black",
                                      command=lambda: self.update_default_color(True))
        self.btn_def_def_clr.grid(row=2, column=2)

        self.lbl_new_ers = Label(self, text="Current eraser color:")
        self.lbl_new_ers.grid(row=3, column=0)
        self.btn_new_ers_clr = TkButton(self, text="Choose eraser color",
                                      command=self.update_eraser_color)
        self.btn_new_ers_clr.grid(row=3, column=1)
        self.btn_def_ers_clr = TkButton(self, bg="white",
                                      activebackground="white",
                                      command=lambda: self.update_eraser_color(True))
        self.btn_def_ers_clr.grid(row=3, column=2)

        self.btn_ok = TkButton(self, text='Ok', command=self.destroy)
        self.btn_ok.grid(row=4, column=1)

    def update_default_color(self, black=False):
        if black:
            self.master.default_color = "black"
            self.lbl_cur_def_clr.configure(bg="black", activebackground="black")
        else:
            color = askcolor(color=self.master.default_color)[1]
            if color is not None:
                self.master.default_color = color
                self.lbl_cur_def_clr.configure(bg=color, activebackground=color)

    def update_eraser_color(self, white=False):
        if white:
            self.master.default_eraser = "white"
            self.lbl_cur_def_clr.configure(bg="white", activebackground="white")
        else:
            color = askcolor(color=self.master.default_color)[1]
            if color is not None:
                self.master.default_eraser = color
                self.lbl_cur_def_clr.configure(bg=color, activebackground=color)
