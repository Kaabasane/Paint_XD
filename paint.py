#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 02:36:29 2022

@author: rugvedm
"""

# pylint: disable=too-many-instance-attributes, too-many-public-methods
# pylint: disable=too-many-statements, too-many-sorcerers, cell-var-from-loop
# pylint: disable=attribute-defined-outside-init, invalid-name, unused-argument
# pylint: disable=expression-not-assigned, fixme

from pathlib import Path
from os import name as os_name

from tkinter import Tk, Menu, messagebox
# from tkinter.ttk import Label, Button, Scale
from tkinter import Button, Spinbox, BooleanVar#, Label
from tkinter.colorchooser import askcolor
from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter.ttk import Notebook
from tkinter.font import nametofont

import pickle

from PIL import Image, ImageTk

from py7zr import SevenZipFile

from helper import ClosableTabFrame, MainConfig, TabConfig, DefaultColorPopup
from helper import FILE_TYPES, CONFIG, CONF_PKL

class Paint:
    def __init__(self):
        self.root = Tk()
        self.root.title("Paint XD")
        if os_name == "nt":
            self.root.state("zoomed")
        elif os_name == "posix":
            self.root.attributes("-zoomed", True)
        else:
            print("Paint not supported on this OS")
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.rowconfigure(2, weight=10)
        self.font = nametofont("TkDefaultFont").actual()

        # Menu ----------------------------------------------------------------

        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.menu = {}

        self.menu["File"] = Menu(self.menubar, tearoff=0)
        self.menu["File"].add_command(label="New", command=self.create_new_tab, accelerator='Ctrl+N', underline=0)
        self.menu["File"].add_separator()
        self.menu["File"].add_command(label="Open", command=self.open_file, accelerator='Ctrl+O', underline=0)
        # https://www.pythontutorial.net/tkinter/tkinter-menu/
        self.recent_tabs_menu = Menu(self.menu["File"], tearoff=0)
        self.menu["File"].add_cascade(label="Open Recent", menu=self.recent_tabs_menu)
        self.menu["File"].add_separator()
        self.menu["File"].add_command(label="Save", command=self.save_file, accelerator='Ctrl+S', underline=0)
        self.menu["File"].add_command(label="Save As..", command=self.save_as_file, accelerator='Ctrl+Shift+S')
        self.menu["File"].add_command(label="Save All", command=self.dummy_func)
        self.menu["File"].add_command(label="Save to PDF", command=self.save_pdf)
        self.menu["File"].add_separator()
        self.menu["File"].add_command(label="Save All & Quit", command=self.dummy_func)
        self.menu["File"].add_command(label="Close All & Quit", command=self.root.destroy)
        self.menu["File"].add_command(label="Quit", command=self.cleanup, accelerator='Ctrl+Q', underline=0)

        self.menu["Edit"] = Menu(self.menubar, tearoff=0)
        self.menu["Edit"].add_command(label="Undo", command=self.dummy_func, accelerator='Ctrl+Z')
        self.menu["Edit"].add_command(label="Redo", command=self.dummy_func, accelerator='Ctrl+Y / Ctrl+Shift+Z')
        self.menu["Edit"].add_separator()
        self.menu["Edit"].add_command(label="Clear", command=self.clear)
        self.menu["Edit"].add_command(label="Fill", command=lambda: self.fill(True))
        self.menu["Edit"].add_command(label="Fill Background", command=self.fill)
        self.menu["Edit"].add_separator()
        self.menu["Edit"].add_command(label="Default Color", command=self.color_default)
        self.menu["Edit"].add_command(label="Change Default Colors", command=self.dummy_func)

        self.menu["Tabs"] = Menu(self.menubar, tearoff=0)
        self.menu["Tabs"].add_command(label="Rename...", command=self.rename_file)
        # TODO: Add these in keyboard shortcuts only, remove from here
        # self.menu["Tabs"].add_command(label="Next Tab", command=lambda: self.change_tab(side=1), accelerator='Ctrl+Tab')
        # self.menu["Tabs"].add_command(label="Prev Tab", command=lambda: self.change_tab(side=-1), accelerator='Ctrl+Shift+Tab')
        self.menu["Tabs"].add_separator()
        self.menu["Tabs"].add_command(label="Close Tab", command=self.close_tab)
        self.menu["Tabs"].add_command(label="Close All Tabs", command=self.close_all)
        self.menu["Tabs"].add_separator()
        self.open_tabs_menu = Menu(self.menu["Tabs"], tearoff=0)
        self.menu["Tabs"].add_cascade(label="Show tab ...", menu=self.open_tabs_menu)

        self.poly_hint = BooleanVar(value=True)
        self.use_icons = BooleanVar(value=False)
        self.menu["Help"] = Menu(self.menubar, tearoff=0)
        self.menu["Help"].add_checkbutton(label="Show Polygon Hint",
                                          command=self.show_poly_hint,
                                          variable=self.poly_hint, onvalue=True,
                                          offvalue=False)
        self.menu["Help"].add_checkbutton(label="Use Cursor Icons (Beta)",
                                          command=self.use_cursor_icons,
                                          variable=self.use_icons, onvalue=True,
                                          offvalue=False)
        self.menu["Help"].add_command(label="About", command=self.dummy_func)
        self.menu["Help"].add_command(label="Keyboard Shortcuts", command=self.dummy_func)

        for name, submenu in self.menu.items():
            self.menubar.add_cascade(label=name, menu=submenu)

        # Widgets -------------------------------------------------------------

        self.pen_button = Button(self.root, text='Pen', command=self.use_pen)
        self.pen_button.grid(row=0, column=0, sticky="ew", padx=10)

        self.brush_button = Button(self.root, text='Brush',
                                   command=self.use_brush)
        self.brush_button.grid(row=0, column=1, sticky="ew", padx=10)

        self.color_button = Button(self.root, text='Color',
                                   command=self.choose_color)
        self.color_button.grid(row=0, column=2, sticky="ew", padx=10)

        self.eraser_button = Button(self.root, text='Eraser',
                                    command=self.use_eraser)
        self.eraser_button.grid(row=0, column=3, sticky="ew", padx=10)

        # TODO: Add a label to the scale
        self.size_scale = Spinbox(self.root, from_=1, to=100)#, showvalue=True,
                                #orient='horizontal')
        self.size_scale.grid(row=0, column=4, sticky="ew", padx=10)

        self.line_button = Button(self.root, text='Line',
                                  command=self.use_line)
        self.line_button.grid(row=1, column=0, sticky="ew", padx=10)

        self.poly_button = Button(self.root, text='Polygon',
                                  command=self.use_poly)
        self.poly_button.grid(row=1, column=1, sticky="ew", padx=10)

        # Tabs ----------------------------------------------------------------
        self.root.update_idletasks()
        self.tabs_control = Notebook(self.root, width=self.root.winfo_width())#, height=int(7.8*(h/10)))
        self.tabs_control.grid(row=2, columnspan=5, sticky="news")
        self.tabs_control.bind('<<NotebookTabChanged>>', self.change_tab)
        self.tabs_control.enable_traversal()

        self.setup()
        self.load_config()
        if not self.tabs:
            self.create_new_tab()
        self.update_default_color_button()

        # Polygon hint
        self.show_poly_hint()

        self.root.mainloop()


    ### Setup
    def setup(self):
        self.old_x, self.old_y = None, None

        self.tab = None
        self.c = None
        self.prev_tab = None

        # Key Bindings
        self.root.bind_all('<Control-Key-s>', self.save_file)
        self.root.bind_all('<Control-Key-S>', self.save_as_file)
        self.root.bind_all('<Control-Key-n>', self.create_new_tab)
        self.root.bind_all('<Control-Key-o>', self.open_file)
        self.root.bind_all('<Escape>', self.poly_reset)

        self.tabs = {}
        self.hidden_tabs = []

    def load_config(self):
        if CONF_PKL.exists():
            with CONF_PKL.open("rb") as file:
                config = pickle.load(file)
            for name, tab in config.tabs.items():
                self.create_new_tab(tab)
            self.font = config.font
            self.poly_hint.set(config.poly_hint)
            self.use_icons.set(config.use_icons)

    def save_config(self):
        config = MainConfig()
        config.font = self.font
        config.poly_hint = self.poly_hint.get()
        config.use_icons = self.use_icons.get()
        CONFIG.mkdir(exist_ok=True)
        for name, tab in self.tabs.items():
            if not tab.hidden:
                config.tabs[name] = TabConfig(tab)
                tab.canvas.postscript(file=CONFIG / f"{name}.eps")

        with CONF_PKL.open("wb") as file:
            pickle.dump(config, file)

    def update_default_color_button(self):
        self.menu["Edit"].entryconfig(
            self.menu["Edit"].index("Default Color"),
            background=self.tab.default_color,
            foreground=self.tab.default_eraser,
            font=(self.font["family"], self.font["size"], 'bold')
        )

    ### Tabs
    def create_new_tab(self, tabconfig=None):
        global gl_cur_tab
        if tabconfig:
            new_tab = tabconfig.name
        else:
            i = 0
            while f"Untitled {i}" in self.tabs:
                i += 1
            new_tab = f"Untitled {i}"

        self.tabs[new_tab] = ClosableTabFrame(self, new_tab)
        self.tab = self.tabs[new_tab]
        self.tabs_control.add(self.tab, text=new_tab)
        self.c = self.tab.canvas

        self.c.bind('<B1-Motion>', self.paint)
        self.use_pen()

        if tabconfig:
            if tabconfig.active_button == "Pen":
                pass #self.use_pen()
            elif tabconfig.active_button == "Brush":
                self.use_brush()
            elif tabconfig.active_button == "Eraser":
                self.use_eraser()
            elif tabconfig.active_button == "Line":
                self.c.unbind('<B1-Motion>')
                self.use_line()
            elif tabconfig.active_button == "Polygon":
                self.c.unbind('<B1-Motion>')
                self.use_poly()
            else:
                print(tabconfig.active_button)

            # FIXME: Image not showing
            self.c.create_image(0, 0, anchor="nw",
                                image=ImageTk.PhotoImage(
                                    Image.open(CONFIG / f"{new_tab}.eps"),
                                    master=self.root
                                ))

        self.c.bind('<ButtonRelease-1>', self.reset)
        self.c.bind('<Button-1>', self.point)

        self.tabs_control.select(self.tab)
        self.update_tabs_list()

    def change_tab(self, event=None):
        # TODO: Just use Prev Active Button instead of Prev Tab if not needed
        if self.prev_tab and self.prev_tab.active_button:
                self.prev_tab.active_button.config(relief='raised')
        self.tab = self.tabs[self.tabs_control.tab(
            self.tabs_control.select(), "text")]
        self.c = self.tab.canvas

        if self.tab.active_button:
            self.tab.active_button.config(relief='sunken')
            if self.tab.active_button["text"] in ("Line", "Polygon"):
                self.c.unbind('<B1-Motion>')
            else:
                self.c.bind('<B1-Motion>', self.paint)
        else:
            self.use_pen()
        self.c.bind('<ButtonRelease-1>', self.reset)
        self.c.bind('<Button-1>', self.point)
        self.prev_tab = self.tab

    def close_tab(self, keep=1):
        if len(self.tabs) > (len(self.hidden_tabs) + keep):
            self.tabs_control.hide(self.tab)
            self.tab.hidden = True
            self.hidden_tabs.append(self.tab.name)
            self.update_tabs_list()
            self.change_tab()

    def update_tabs_list(self):
        self.open_tabs_menu.delete(0, 'end')
        self.recent_tabs_menu.delete(0, 'end')
        for tab in self.tabs:
            if tab not in self.hidden_tabs:
                self.open_tabs_menu.add_command(
                    label=tab, command=lambda tab=tab: self.show_tab(tab))
            else:
                self.recent_tabs_menu.add_command(
                    label=tab, command=lambda tab=tab: self.show_tab(tab))

    def show_tab(self, tab_name):
        tab = self.tabs[tab_name]
        if tab.hidden:
            self.hidden_tabs.remove(tab_name)
            tab.hidden = False
            self.tabs_control.add(tab)
        else:
            self.tabs_control.select(tab)

        self.update_tabs_list()

    def close_all(self):
        while len(self.tabs) != len(self.hidden_tabs):
            self.close_tab(keep=0)

    ### Tools
    def use_pen(self):
        self.tab.activate_button(self.pen_button)

    def use_brush(self):
        self.tab.activate_button(self.brush_button)

    def use_line(self):
        self.tab.activate_button(self.line_button)

    def use_poly(self):
        self.tab.activate_button(self.poly_button)

    def choose_color(self):
        color = askcolor(color=self.tab.color)[1]
        if color is not None:
            self.tab.color = color

    # TODO: Change DefaultColorPopup for tabs
    def change_default_colors(self):
        self.popup = DefaultColorPopup(self.root)

        # if self.popup.filename:
        #     filepng = self.popup.filename + '.png'

        #     if not os.path.exists(filepng) or \
        #             messagebox.askyesno("File already exists", "Overwrite?"):
        #         fileps = self.popup.filename + '.eps'
        #         self.c.postscript(file=fileps)
        #         Image.open(fileps).save(filepng, 'png')
        #         os.remove(fileps)

        #         messagebox.showinfo("File Save", "File saved!")
        #     else:
        #         messagebox.showwarning("File Save", "File not saved!")
        # else:
        #     messagebox.showwarning("File Save", "File name empty!")

    def use_eraser(self):
        self.tab.activate_button(self.eraser_button, eraser_mode=True)

    def size_multiplier(self):
        return 2.5 if self.tab.active_button["text"] == "Brush" else 1

    ### Canvas
    # TODO: Can we use polygon approach of create_line?
    def paint(self, event):
        line_width = float(self.size_scale.get()) * self.size_multiplier()
        paint_color = (self.tab.default_eraser if self.tab.eraser_on
                       else self.tab.color)
        if self.old_x and self.old_y:
            self.c.create_line(self.old_x, self.old_y, event.x, event.y,
                               width=line_width, fill=paint_color,
                               capstyle='round')
        else:
            self.c.create_line(event.x, event.y, event.x, event.y,
                               width=line_width, fill=paint_color,
                               capstyle='round')
        self.old_x = event.x
        self.old_y = event.y

    # TODO: Maybe try to use line hint like in MS Paint
    # Maybe continuously creating and deleting the line would be the key
    def line(self, x, y, line_width):
        paint_color = (self.tab.default_eraser if self.tab.eraser_on
                       else self.tab.color)
        self.c.create_line(self.old_x, self.old_y, x, y,
                           width=line_width, fill=paint_color,
                           capstyle=self.tab.capstyle)

    def point(self, event):
        btn = self.tab.active_button["text"]
        line_width = float(self.size_scale.get())
        paint_color = (self.tab.default_eraser if self.tab.eraser_on
                       else self.tab.color)
        if btn in ("Line", "Polygon"):
            if None not in (self.old_x, self.old_y):
                self.line(event.x, event.y, line_width)
                self.old_x, self.old_y = ((None, None) if btn == 'Line'
                                          else (event.x, event.y))
            else:
                self.old_x, self.old_y = (event.x, event.y)
        else:
            self.c.create_line(event.x, event.y, event.x, event.y,
                               width=line_width * self.size_multiplier(),
                               fill=paint_color, capstyle='round')
            self.old_x = event.x
            self.old_y = event.y


    def reset(self, event=None):
        if self.tab.active_button["text"] not in ("Line", "Polygon"):
            self.old_x, self.old_y = None, None

    def poly_reset(self, event=None):
        self.old_x, self.old_y = None, None

    def color_default(self):
        self.tab.color = self.tab.default_color

    def clear(self):
        self.c.delete("all")
        self.reset()

    def fill(self, clear=False):
        if clear:
            self.c.delete("all")
        color = askcolor(color=self.tab.color)[1]
        if color is not None:
            self.c.configure(bg=color)

    ### Save
    def save_file(self, event=None):
        path = self.tab.path
        if path is not None:
            fileps = Path(path + '.eps')
            self.c.postscript(file=fileps)
            if not path.endswith(".eps"):
                Image.open(fileps).save(path)
                fileps.unlink()
        else:
            self.tabs_control.tab("current",
                                  text=self.save_as_file())

    # TODO: Provide hint/suggestion that file name would be Untitled Xn when saving
    def save_as_file(self, event=None):
        file = asksaveasfile(filetypes=FILE_TYPES,
                             defaultextension=FILE_TYPES[0][1][1:])
        if file:
            fileps = Path(file.name + '.eps')
            self.c.postscript(file=fileps)
            if not file.name.endswith(".eps"):
                Image.open(fileps).save(file.name)
                fileps.unlink()
            # TODO: Check if name already exists
            new_name = Path(file.name).name
            self.tabs[new_name] = self.tabs.pop(self.tab.name)
            self.tab.name = new_name
            self.tab.path = file.name
            return new_name
        else:
            return self.tab.name

    def save_pdf(self):
        file = asksaveasfile(filetypes=(('PDF', '*.pdf')),
                             defaultextension=".pdf")
        fileps = Path(file.name + '.eps')
        self.c.postscript(file=fileps)
        Image.open(fileps).save(file.name, 'pdf')
        fileps.unlink()

    def open_file(self):
        self.create_new_tab()
        self.tab.canvas.create_image(0, 0, anchor="nw",
                                     image=ImageTk.PhotoImage(
                                         Image.open(askopenfilename()),
                                         master=self.root
                                     ))

    ### Misc
    # TODO: Dummy
    def dummy_func(self):
        pass

    def rename_file(self):
        new_name = messagebox.askquestion("Rename File", self.tab.name)
        if new_name in ["end", "last", "none", "active"]:
            messagebox.showinfo("Rename",
                                f"You can't use '{new_name}' as name.")
        elif new_name:
            self.tabs[new_name] = self.tabs.pop(self.tab.name)
            self.tab.name = new_name
            if self.tab.path:
                path = Path(self.tab.path)
                path.replace(path.parent / new_name)
        else:
            messagebox.showinfo("Rename", "Rename Failed.")

    def show_poly_hint(self):
        if self.poly_hint.get():
            messagebox.showinfo("Polygon Hint",
                                "Press 'Escape' to end polygon.\nYou can "
                                "disable this hint in the 'About' menu.")

    def use_cursor_icons(self):
        if self.use_icons.get():
            if self.tab.active_button["text"] == "Pen":
                self.c.config(cursor="pencil")
            elif self.tab.active_button["text"] == "Brush":
                self.c.config(cursor="dot")
            elif self.tab.active_button["text"] == "Eraser":
                self.c.config(cursor="dot white black")
            else:
                self.c.config(cursor="arrow")
        else:
            self.c.config(cursor="arrow")

    def cleanup(self):
        self.root.quit()
        self.save_config()
        self.root.destroy()

if __name__ == '__main__':
    Paint()
