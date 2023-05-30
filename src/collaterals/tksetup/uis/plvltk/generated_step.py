#!/usr/bin/env python

from tkinter import *
import threading
import multiprocessing
import time

from src.lib.toolkit.validationlanguage.src_translator.trans_h2l import *
from src.lib.toolkit.validationlanguage.src_translator.trans_l2p import *

import utils
import setting


RUNNING_THREAD = None
TCD_NAME = None


def __output():
    output = os.path.join(os.getcwd(), 'plvltk_output')
    if not os.path.exists(output): os.makedirs(output)
    return output


def __tcdname(tcd, stamp, text):
    if stamp.get():
        timestamp = '_' + time.strftime('%Y%m%d%H%M%S')
    else:
        timestamp = ''

    tcdname = tcd.get()
    if not tcdname:
        text.insert(END, f'TCD Name cannot be empty')
        return

    return tcdname + timestamp


def __h2l_translate_line(line):
    translator = HlsTranslator()
    outlines = translator.translate_lines([line])
    return outlines


def __l2py_translate_line(line):
    translator = PythonTransaltor()
    outlines = translator.translate_lines_only([line])
    return outlines


def __h2l_translate_file(input, output):
    translator = HlsTranslator()
    translator.translate_file(input, output)


def __l2py_translate_file(input, output):
    bios_menu = BiosMenuTranslator(setting.vldata.default_pvl_mapping_file)
    bios_menu_config = os.path.join(__output(), setting.vldata.bios_knob_config_module+'.py')
    bios_menu.translate_to_file(bios_menu_config)

    translator = PythonTransaltor()
    translator.translate_file(input, output)


def h2l(tcd, stamp, step, text):
    global TCD_NAME

    tcdname = __tcdname(tcd, stamp, text)
    TCD_NAME = tcdname

    text.insert(END, '===== (HLS -> LLS) Translation Start   =====\n\n')

    lines = step.get('1.0', END).split('\n')

    hls = os.path.join(__output(), f'{tcdname}.hls')
    with open(hls, 'w') as fp:
        fp.writelines([line + '\n' for line in lines])

    lls = os.path.join(__output(), f'{tcdname}.lls')

    if not ''.join(lines):
        text.insert(END, 'Required: Pick up steps from left panel\n')
        return

    for line in lines:
        if line:
            text.insert(END, f'[HLS] {line}\n')
            results = __h2l_translate_line(line)

            for r in results:
                text.insert(END, f' =>[LLS] {r}\n')
            text.insert(END, '\n')
        __h2l_translate_file(hls, lls)

    text.insert(END, '===== (HLS -> LLS) Translation End   =====\n\n')


def l2py(text):
    text.insert(END, '===== (LLS -> PYTHON) Translation Start   =====\n\n')

    lls = os.path.join(__output(), f'{TCD_NAME}.lls')
    if not os.path.exists(lls):
        text.insert(END, f'Required: Generate {TCD_NAME}.lls with <H2L> button\n')
        return

    py = os.path.join(__output(), f'{TCD_NAME}.py')

    lines = open(lls, 'r').readlines()
    for line in lines:
        if line:
            text.insert(END, f'[LLS] {line}\n')
            results = __l2py_translate_line(line)

            for r in results:
                text.insert(END, f' =>[PYTHON] {r}\n')
            text.insert(END, '\n')

    __l2py_translate_file(lls, py)

    text.insert(END, '===== (LLS -> PYTHON) Translation END   =====\n\n')


def h2py(tcd, stamp, step, text):
    h2l(tcd, stamp, step, text)
    l2py(text)


def exec_python(text):
    global RUNNING_THREAD

    text.insert(END, '===== Run Test Script Start   =====\n\n')

    py = os.path.join(__output(), f'{TCD_NAME}.py')
    if not os.path.exists(py):
        text.insert(END, f'Required: Generate {TCD_NAME}.py with <H2L->L2PY, or H2PY> button\n')
        return

    RUNNING_THREAD = utils.TestThread(cmd=f'python {py}', text=text)


def stop_python(text):
    if RUNNING_THREAD:
        RUNNING_THREAD.stop()

        py = os.path.join(__output(), f'{TCD_NAME}.py')
        text.insert(END, f'Test Script: {os.path.basename(py)} is terminated by user ...\n')
    else:
        text.insert(END, f'No any running script here ...\n')