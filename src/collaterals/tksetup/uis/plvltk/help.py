#!/usr/bin/env python

from tkinter.messagebox import *

import webbrowser


def about():
    showinfo(title='About Me', message='Developed by PAIV SH PV Team\n\nUsed for HLS Steps Dryrun')


def hls_wiki():
    webbrowser.open('https://wiki.ith.intel.com/display/testing/Tools')



def toolkit_wiki():
    webbrowser.open('https://wiki.ith.intel.com/display/testing/Automation+Validation+Toolkit+Document')
