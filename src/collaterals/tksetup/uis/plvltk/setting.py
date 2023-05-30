#!/usr/bin/env python

import src.lib.toolkit.validationlanguage.src_translator.const as vldata
from src.lib.toolkit.validationlanguage.src_translator.trans_h2l import get_pvl_mapping_file_path
from src.lib.toolkit.basic.config import *

import win32com.client as win32
import os


def set_sut():
    os.system(DEFAULT_SUT_CONFIG_FILE)


def set_feature():
    pvl = get_pvl_mapping_file_path()
    # excel = win32.gencache.EnsureDispatch('Excel.Application')
    # excel.Visible = True
    # excel.Workbooks.Open(pvl)

    os.system(pvl)


def set_debug():
    os.system(DEFAULT_DEBUG_CONFIG_FILE)


def set_tool():
    os.system(DEFAULT_TOOL_CONFIG_FILE)