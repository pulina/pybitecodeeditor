#!/usr/bin/python
# -*- coding: utf-8 -*-

import tkFileDialog
import tkMessageBox
import types
import struct
import marshal
import time

from Tkinter import *
from ttk import *
from ScrolledText import *


class Application:
    root = None
    decompilat = None
    frame = None
    const_frame = None
    info_frame = None
    code_frame = None
    current_code = None
    tree = None
    tree_binding = {}

    allowed_types = ("Compiled python file", "*.pyc"),

    class Decompilat:
        decompilat_file = None
        magic_number = None
        compilation_date = None
        code = None

        def __init__(self, decompilat_file, magic_number, compilation_date, code):
            self.decompilat_file = decompilat_file
            self.magic_number = magic_number
            self.compilation_date = compilation_date
            self.code = code

        def get_codes(self):
            return self.code.get_codes()

    class Code:
        argcount = None
        nlocals = None
        stacksize = None
        flags = None
        code = None
        consts = None
        names = None
        varnames = None
        freevars = None
        cellvars = None
        filename = None
        name = None
        lnotab = None

        def __init__(self, argcount, nlocals, stacksize, flags, code, consts, names, varnames, freevars, cellvars,
                     filename,
                     name, lnotab):
            self.argcount = argcount
            self.nlocals = nlocals
            self.stacksize = stacksize
            self.flags = flags
            self.code = code
            self.consts = consts
            self.names = names
            self.varnames = varnames
            self.freevars = freevars
            self.cellvars = cellvars
            self.filename = filename
            self.name = name
            self.lnotab = lnotab

        def get_codes(self):
            codes = {self: []}
            for c in self.consts:
                if isinstance(c, self.__class__):
                    codes[self].append(c.get_codes())
            return codes

        def __str__(self):
            return "<code name='{}'>".format(self.code)

        def show_hex(self):
            return self.code.co_code.encode('hex')

    class DocompilatFabric():

        @classmethod
        def fabric(cls, file):

            magic = file.read(4)
            mod_time = file.read(4)
            try:
                mod_time = time.asctime(time.localtime(struct.unpack('E', mod_time)[0]))
            except:
                mod_time = time.asctime(time.localtime(struct.unpack('i', mod_time)[0]))
            marshal_obj = marshal.load(file)
            payload = {
                'decompilat_file': file,
                'magic_number': magic,
                'compilation_date': mod_time,
                'code': cls.fabric_code(marshal_obj)
            }
            Application.decompilat = Application.Decompilat(**payload)
            Application.current_code = payload['code']

        @classmethod
        def fabric_code(cls, code):
            consts = []
            for const in code.co_consts:
                if isinstance(const, types.CodeType):
                    consts.append(cls.fabric_code(const))
                else:
                    consts.append(const)
            payload = {
                'argcount': code.co_argcount,
                'nlocals': code.co_nlocals,
                'stacksize': code.co_stacksize,
                'flags': code.co_flags,
                'names': code.co_names,
                'varnames': code.co_varnames,
                'freevars': code.co_freevars,
                'cellvars': code.co_cellvars,
                'filename': code.co_filename,
                'name': code.co_name,
                'lnotab': code.co_lnotab,
                'consts': consts,
                'code': code
            }
            return Application.Code(**payload)

    class MainFrame(Frame):
        def __init__(self, parent):
            Frame.__init__(self, parent)

            self.parent = parent
            self.initUI()

        def initUI(self):
            self.pack(fill=BOTH, expand=True)

            self.columnconfigure(1, weight=1)
            self.columnconfigure(2, weight=7)
            self.columnconfigure(3, pad=2, weight=1)
            self.rowconfigure(1, weight=5)
            self.rowconfigure(2, weight=5)

            Application.prepere_interface(self, Application.current_code)

    @staticmethod
    def _iter_tree(code_tree, parent=""):
        for x, y in code_tree.iteritems():
            new_parent = Application.tree.insert(parent, "end", str(x), text=x.name)
            Application.tree_binding[new_parent] = x
            for z in y:
                Application._iter_tree(z, new_parent)

    @staticmethod
    def tree_select(event):
        Application.prepere_interface(Application.frame, Application.tree_binding[Application.tree.selection()[0]])

    @classmethod
    def prepere_interface(cls, frame, code):
        
        if code:

            cls.tree = Treeview(frame)
            ysb = Scrollbar(orient=VERTICAL, command=cls.tree.yview)
            xsb = Scrollbar(orient=HORIZONTAL, command=cls.tree.xview)
            cls.tree['yscroll'] = ysb.set
            cls.tree['xscroll'] = xsb.set
            cls.tree.bind('<<TreeviewSelect>>', cls.tree_select)
            cls._iter_tree(cls.decompilat.get_codes())
            cls.current_code = code

            cls.tree.grid(column=0, row=1, rowspan=2, sticky=E + W + S + N, pady=2, padx=5)

            cls.code_frame = ScrolledText(frame)
            cls.code_frame.grid(row=1, column=1, rowspan=2, padx=1, sticky=E + W + S + N)
            cls.print_code()

            cls.info_frame = Listbox(frame)
            cls.info_frame.grid(row=1, column=2, pady=2, padx=2, sticky=E + W + S + N)
            cls.print_info()

            cls.const_frame = Listbox(frame)
            cls.const_frame.grid(row=2, column=2, pady=2, padx=2, sticky=E + W + S + N)
            cls.print_consts()

    @staticmethod
    def print_code():
        Application.code_frame.insert('1.0', Application.current_code.show_hex())

    @staticmethod
    def print_info():
        to_show = ['argcount', 'nlocals', 'stacksize', 'flags', 'names', 'varnames', 'freevars', 'cellvars', 'filename',
                   'name', 'lnotab']
        for x in to_show:
            Application.info_frame.insert(END, "{} = {}".format(x, getattr(Application.current_code, x)))

    @staticmethod
    def print_consts():
        for number, x in enumerate(Application.current_code.consts):
            Application.const_frame.insert(END, '{} : {}'.format(number, x))

    @classmethod
    def prepere_root(cls):
        Application.root = Tk(className="Python bytecode simply editor")
        w, h = Application.root.winfo_screenwidth(), Application.root.winfo_screenheight()
        Application.root.geometry("%dx%d+0+0" % (w, h))

    @classmethod
    def prepere_main_frame(cls):
        Application.frame = Application.MainFrame(Application.root)

    @classmethod
    def prepere_menu(cls):
        menu = Menu(Application.root)
        Application.root.config(menu=menu)
        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=Application.open_command)
        file_menu.add_command(label="Save", command=Application.save_command)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=Application.exit_command)

    @classmethod
    def main(cls):
        Application.prepere_root()
        Application.prepere_main_frame()
        Application.prepere_menu()
        Application.root.mainloop()

    @classmethod
    def open_command(cls):
        pyc_file = tkFileDialog.askopenfile(parent=Application.root, mode='rb', title='Select a file',
                                            filetypes=Application.allowed_types)
        if pyc_file:
            cls.DocompilatFabric.fabric(pyc_file)
            Application.prepere_main_frame()
            pyc_file.close()

    @classmethod
    def save_command(self):
        # file = tkFileDialog.asksaveasfile(mode='w')
        # if file != None:
        #     data = self.textPad.get('1.0', END + '-1c')
        #     file.write(data)
        #     file.close()
        pass

    @classmethod
    def exit_command(cls):
        if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
            Application.root.destroy()


if __name__ == '__main__':
    Application.main()
