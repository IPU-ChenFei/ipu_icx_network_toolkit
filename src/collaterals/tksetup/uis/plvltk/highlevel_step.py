#!/usr/bin/env python

from tkinter import *
from tkinter import ttk
from tkinter.messagebox import *

from functools import partial

import setting

from src.lib.toolkit.validationlanguage.src_translator.parser_table import MappingTableParser


def __new_tmp_frame(frame):
    hls_tmp_frame = Frame(frame, width=300, height=320, background='lightblue')
    hls_tmp_frame.grid(row=0, column=1, sticky='nwes', padx=5)
    hls_tmp_frame.grid_propagate(False)
    return hls_tmp_frame


def boot_to(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        os = value.get()
        if os:
            text.insert(END, f'{setting.vldata.OP_BOOT_TO}: {os}\n')

    value = StringVar()
    value.set('Windows')
    Label(hls_tmp_frame, text='Environment', anchor='w', width=4).grid(row=0, column=0, rowspan=4, padx=5, sticky='wens')
    Radiobutton(hls_tmp_frame, text='Windows', anchor='w', variable=value, value='Windows').grid(row=0, column=1, padx=5, sticky='we')
    Radiobutton(hls_tmp_frame, text='Linux', anchor='w', variable=value, value='Linux').grid(row=1, column=1, padx=5, sticky='we')
    Radiobutton(hls_tmp_frame, text='ESXI', anchor='w', variable=value, value='ESXI').grid(row=2, column=1, padx=5, sticky='we')
    Radiobutton(hls_tmp_frame, text='UEFI SHELL', anchor='w', variable=value, value='UEFI SHELL').grid(row=3, column=1, padx=5, sticky='we')

    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky='we')


def reset_to(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        os = value.get()
        if os:
            text.insert(INSERT, f'{setting.vldata.OP_RESET_TO}: {os}\n')

    value = StringVar()
    value.set('OS')
    Label(hls_tmp_frame, text='Environment', anchor='w', width=4).grid(row=0, column=0, rowspan=2, padx=5, sticky='wens')
    Radiobutton(hls_tmp_frame, text='OS', anchor='w', variable=value, value='OS').grid(row=0, column=1, padx=5, sticky='we')
    Radiobutton(hls_tmp_frame, text='UEFI SHELL', anchor='w', variable=value, value='UEFI SHELL').grid(row=1,column=1, padx=5, sticky='we')

    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='we')


def set_feature(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, feature):
        item = feature.get(0, END)
        value = ''
        for i in item:
            value += f'{i}, '
        if value:
            text.insert(END, f'{setting.vldata.OP_SET_FEATURE}: {value.strip(", ")}\n')

    mapping_table = MappingTableParser('pvl.xlsx')
    feature_table = mapping_table.feature_table

    # read feature table
    feature_pair = {}
    for k, v in feature_table.keys():
        if k not in feature_pair.keys():
            feature_pair.update({k: [v]})
        else:
            if k not in feature_pair[k]:
                feature_pair[k].append(v)

    ttk.Label(hls_tmp_frame, text='Feature Name').grid(row=0, column=0, padx=5, sticky='we')
    ttk.Label(hls_tmp_frame, text='Feature Option').grid(row=0, column=1, padx=5, sticky='we')
    name = ttk.Combobox(hls_tmp_frame, width=12, values=list(feature_pair.keys()))
    name.grid(row=1, column=0, padx=5, sticky='we')
    value = ttk.Combobox(hls_tmp_frame, width=12, postcommand=lambda : value.config(values=list(feature_pair[name.get()])) if name.get() else '')
    value.grid(row=1, column=1, padx=5, sticky='we')

    feature = Listbox(hls_tmp_frame)
    feature.grid(row=2, column=0, columnspan=5, padx=5, sticky='we')
    ttk.Button(hls_tmp_frame, width=2, text='+', command=lambda : feature.insert(END, f'{name.get()} = {value.get()}') if name.get() and value.get() else '').grid(row=1, column=2, padx=5, sticky='we')
    ttk.Button(hls_tmp_frame, width=2,text='-', command=lambda : feature.delete(feature.curselection()) if feature.curselection() else '').grid(row=1, column=3, sticky='we')
    ttk.Button(hls_tmp_frame, width=2, text='c', command=lambda: feature.delete(0, END)).grid(row=1, padx=5, column=4, sticky='we')

    scrollbar_v = Scrollbar(feature, orient='vertical')
    scrollbar_v.pack(side='right', fill='both')
    scrollbar_v.config(command=feature.yview)
    feature.config(yscrollcommand=scrollbar_v.set)

    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, feature))
    add_step.grid(row=3, column=0, columnspan=5, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=4, column=0, columnspan=5, padx=5, pady=5, sticky='we')


def run_tcd_block(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, block_entry, repeat_entry):
        block = block_entry.get()
        repeat = repeat_entry.get()
        repeat = repeat if repeat else 1

        if block:
            text.insert(END, f'{setting.vldata.OP_TCDB}: {block}, repeat={repeat}\n')

    ttk.Label(hls_tmp_frame, text='Block File', anchor='w', width=4).grid(row=0, column=0, padx=5, sticky='wens')
    block_entry = ttk.Entry(hls_tmp_frame)
    block_entry.insert(0, 'test_tcdb')
    block_entry.grid(row=0, column=1, padx=5, sticky='we')

    ttk.Label(hls_tmp_frame, text='Repeat', anchor='w', width=4).grid(row=1, column=0, padx=5, pady=5, sticky='wens')
    repeat_entry = ttk.Entry(hls_tmp_frame)
    repeat_entry.insert(0, '1')
    repeat_entry.grid(row=1, column=1, padx=5, sticky='we')

    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, block_entry, repeat_entry))
    add_step.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=3, column=0, columnspan=2, padx=5,
    #                                                                             pady=5, sticky='we')

def execute_command(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, set_timeout, timeout_entry, set_assert0, command_entry):
        timeout = None
        nocheck = False

        if set_timeout.get():
            timeout = timeout_entry.get()
        if not set_assert0.get():
            nocheck = True

        command = command_entry.get()
        if not command: raise  # cannot run empty command

        if nocheck:
            command = f'nocheck, ' + command
        if timeout:
            command = f'timeout={int(timeout)}, ' + command

        text.insert(END, f'{setting.vldata.OP_EXECUTE_CMD}: {command}\n')

    Label(hls_tmp_frame, text='Command', anchor='w').grid(row=0, column=0, padx=5, sticky='wens')
    command_entry = Entry(hls_tmp_frame)
    command_entry.insert(0, 'ls /root')
    command_entry.grid(row=0, column=1, padx=5, columnspan=3, sticky='we', pady=1)

    set_timeout = BooleanVar()
    set_timeout.set(False)
    set_assert0 = BooleanVar()
    set_assert0.set(True)

    ttk.Checkbutton(hls_tmp_frame, text='Timeout', variable=set_timeout, onvalue=True, offvalue=False).grid(row=1, column=0, padx=5, pady=5, sticky='we')
    timeout_entry = ttk.Entry(hls_tmp_frame, width=12)
    timeout_entry.insert(0, '180')
    timeout_entry.grid(row=1, column=1, padx=5, sticky='we')
    ttk.Checkbutton(hls_tmp_frame, text='Assert Retval == 0', variable=set_assert0, onvalue=True, offvalue=False).grid(row=1, column=2, padx=5, sticky='we')

    ttk.Label(hls_tmp_frame, text='Constants').grid(row=2, column=0, padx=5, sticky='we')

    constants = ttk.Combobox(hls_tmp_frame, values=[
        '',
        'sutos.bkc_root_path'])
    constants.grid(row=2, column=1, columnspan=2, padx=5, sticky='we')

    constants.bind(
        '<<ComboboxSelected>>',
        lambda e: command_entry.insert(END, '{' + constants.get() + '}' if constants.get() else '')
    )

    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, set_timeout, timeout_entry, set_assert0, command_entry))
    add_step.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky='we')


def execute_host_command(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, set_timeout, timeout_entry, set_assert0, command_entry):
        timeout = None
        nocheck = False

        if set_timeout.get():
            timeout = timeout_entry.get()
        if not set_assert0.get():
            nocheck = True

        command = command_entry.get()
        if not command: raise  # cannot run empty command

        if nocheck:
            command = f'nocheck, ' + command
        if timeout:
            command = f'timeout={int(timeout)}, ' + command

        text.insert(END, f'{setting.vldata.OP_EXECUTE_HOST_CMD}: {command}\n')

    Label(hls_tmp_frame, text='Command', anchor='w').grid(row=0, column=0, padx=5, sticky='wens')
    command_entry = Entry(hls_tmp_frame)
    command_entry.insert(0, 'dir C:\\')
    command_entry.grid(row=0, column=1, padx=5, columnspan=3, sticky='we', pady=1)

    set_timeout = BooleanVar()
    set_timeout.set(False)
    set_assert0 = BooleanVar()
    set_assert0.set(True)

    ttk.Checkbutton(hls_tmp_frame, text='Timeout', variable=set_timeout, onvalue=True, offvalue=False).grid(row=1,
                                                                                                            column=0,
                                                                                                            padx=5,                                                                                         pady=5,
                                                                                                            sticky='we')

    timeout_entry = ttk.Entry(hls_tmp_frame, width=12)
    timeout_entry.insert(0, '180')
    timeout_entry.grid(row=1, column=1, padx=5, sticky='we')
    ttk.Checkbutton(hls_tmp_frame, text='Assert Retval == 0', variable=set_assert0, onvalue=True, offvalue=False).grid(
        row=1, column=2, padx=5, sticky='we')

    ttk.Label(hls_tmp_frame, text='Constants').grid(row=2, column=0, padx=5, sticky='we')

    constants = ttk.Combobox(hls_tmp_frame, values=[
        '',
        'hostos.bkc_root_path',
        'bmc.ipaddr',
        'bmc.username',
        'bmc.password'])
    constants.grid(row=2, column=1, columnspan=2, padx=5, sticky='we')

    constants.bind(
        '<<ComboboxSelected>>',
        lambda e: command_entry.insert(END, '{' + constants.get() + '}' if constants.get() else '')
    )

    add_step = Button(hls_tmp_frame, text='Add Step', width=40,
                      command=partial(__add_step, text, set_timeout, timeout_entry, set_assert0, command_entry))
    add_step.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=4, column=0, columnspan=3, padx=5,
    #                                                                             pady=5, sticky='we')


def execute_itp_command(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, entry):
        value = entry.get()
        if value:
            text.insert(END, f'{setting.vldata.OP_ITP_CMD}: {value}\n')

    ttk.Label(hls_tmp_frame, text='Command', anchor='w', width=4).grid(row=0, column=0, padx=5, sticky='wens')
    entry = Entry(hls_tmp_frame)
    entry.insert(0, 'itp.unlock()')
    entry.grid(row=0, column=1, padx=5, sticky='we')
    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, entry))
    add_step.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=2, column=0, columnspan=2, padx=5,
    #                                                                             pady=5, sticky='we')

def wait(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, entry):
        value = entry.get()
        if value:
            text.insert(END, f'{setting.vldata.OP_WAIT}: {value}\n')

    ttk.Label(hls_tmp_frame, text='Second', anchor='w', width=4).grid(row=0, column=0, padx=5, sticky='wens')
    entry = ttk.Entry(hls_tmp_frame)
    entry.insert(0, '30')
    entry.grid(row=0, column=1, padx=5, sticky='we')
    add_step = Button(hls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, entry))
    add_step.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(hls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=2, column=0, columnspan=2, padx=5,
    #                                                                             pady=5, sticky='we')


def clear_cmos(frame, text):
    hls_tmp_frame = __new_tmp_frame(frame)

    text.insert(END, f'Clear CMOS:\n')