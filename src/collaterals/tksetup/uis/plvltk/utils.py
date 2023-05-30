#!/usr/bin/env python

from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *
from tkinter.messagebox import showinfo

import subprocess
import os
import time
import sys
import signal
import threading


# basic style definition
TITLE_FONT = '"Arial Black" 10 bold'
STRONG_FONT = 'Consolas 14 bold'
HIGHLIGHT_FONT = 'Consolas 30 bold'


class TextMonitor(Text):
    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)

    def insert(self, index, chars, *args):
        super().insert(index, chars, *args)
        self.see(END)


class TestThread(threading.Thread):
    def __init__(self, cmd, cwd=os.getcwd(), timeout=None, text=None):
        super().__init__(daemon=True)
        self.is_stop = False
        self.cmd = cmd
        self.cwd = cwd
        self.timeout = timeout
        self.text = text
        self.start()

    def run_cmd(self, cmd, cwd=None, timeout=None, text=None):
        print(f'EXEC: {cmd} in {cwd}')
        text.insert(END, f'EXEC: {cmd} in {cwd}\n')

        cwd = cwd if cwd else os.getcwd()
        timeout = int(timeout) if timeout else sys.maxsize

        ret = -1
        output = ''

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            cwd=cwd
        )

        self.pid = proc.pid

        now = time.time()
        while time.time() - now < timeout:
            ret = proc.poll()
            if ret is None:
                data = proc.stdout.readline().decode()
                sys.stdout.write(data)
                sys.stdout.flush()

                # print to text widget
                if text:
                    text.insert(END, data)

                output += data
                continue
            break
        else:
            print(f'EXEC: {cmd} timeout in {timeout}s')

        self.pid = -sys.maxsize - 1
        return ret, output

    def run(self):
        self.run_cmd(self.cmd, self.cwd, self.timeout, self.text)

    def stop(self):
        if self.pid > 0:
            print(f'kill: {self.pid}')
            os.kill(self.pid, signal.SIGTERM)


class ToolTip:
    def __init__(self, widget, text, timeout=500, offset=(0, -20), **kw):
        self.widget = widget
        self.text = text
        self.offset = offset
        self._init_params()
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def _init_params(self):
        self.id_after = None
        self.x, self.y = 0, 0
        self.tipwindow = None
        self.background = 'lightyellow'

    def cursor(self, event):
        self.x = event.x
        self.y = event.y

    def tip_window(self):
        window = Toplevel(self.widget)
        window.overrideredirect(True)
        x = self.widget.winfo_rootx() + self.x + self.offset[0]
        y = self.widget.winfo_rooty() + self.y + self.offset[1]
        window.wm_geometry("+%d+%d" % (x, y))
        return window

    def showtip(self):
        params = {
            'text': self.text,
            'justify': 'left',
            'background': self.background,
            'relief': 'solid',
            'borderwidth': 1
        }
        self.tipwindow = self.tip_window()
        label = Label(self.tipwindow, **params)
        label.grid(sticky='nsew')

    def enter(self, event):
        self.cursor(event)
        self.showtip()

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
        else:
            self.tipwindow = None

    def leave(self, event):
        self.hidetip()


class TextPopup:
    @staticmethod
    def copy(editor, event=None):
        editor.event_generate('<<Copy>>')

    @staticmethod
    def cut(editor, event=None):
        editor.event_generate('<<Cut>>')

    @staticmethod
    def paste(editor, event=None):
        editor.event_generate('<<Paste>>')

    @staticmethod
    def clear(editor, event=None):
        editor.delete('1.0', END)

    @staticmethod
    def save(editor, event=None):
        file = filedialog.asksaveasfile()
        if file:
            file.write(editor.get('1.0', END))
            file.close()

    @staticmethod
    def right_click(menu, editor, event):
        menu.delete(0, END)
        menu.add_command(label='Cut', command=lambda: TextPopup.cut(editor))
        menu.add_command(label='Copy', command=lambda: TextPopup.copy(editor))
        menu.add_command(label='Paste', command=lambda: TextPopup.paste(editor))
        menu.add_command(label='Clear', command=lambda: TextPopup.clear(editor))
        menu.add_command(label='Save As', command=lambda: TextPopup.save(editor))
        menu.post(event.x_root, event.y_root)

    @staticmethod
    def bios_right_click(menu, editor, event):
        menu.delete(0, END)
        menu.add_command(label='Start BIOS Log', command=None)
        menu.add_command(label='Stop BIOS Log', command=None)
        menu.add_command(label='Cut', command=lambda: TextPopup.cut(editor))
        menu.add_command(label='Copy', command=lambda: TextPopup.copy(editor))
        menu.add_command(label='Paste', command=lambda: TextPopup.paste(editor))
        menu.add_command(label='Clear', command=lambda: TextPopup.clear(editor))
        menu.add_command(label='Save As', command=lambda: TextPopup.save(editor))
        menu.post(event.x_root, event.y_root)
