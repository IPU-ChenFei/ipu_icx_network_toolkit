#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
from src.lib.validationlanguage.gui.mfunc.main_ui import *

if __name__ == '__main__':
    app = wx.App()
    frm = MainFrame(None, globals(), locals())
    frm.Show() 
    app.MainLoop()
