#!/usr/bin/env python

from tkinter import *
from tkinter.messagebox import *

import setting

from functools import partial


def __new_tmp_frame(frame):
    lls_tmp_frame = Frame(frame, width=300, height=415, bg='lightblue')
    lls_tmp_frame.grid(row=0, column=1, sticky='nwes', padx=5)
    lls_tmp_frame.grid_propagate(False)
    return lls_tmp_frame


def check_environment(frame, text):
    lls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        os = value.get()
        if os:
            text.insert(INSERT, f'{setting.vldata.OP_CHECK_ENVIRONMENT}: {os}\n')

    value = StringVar()
    value.set('OS')
    Label(lls_tmp_frame, text='Environment', anchor='w', width=4).grid(row=0, column=0, rowspan=2, padx=5, sticky='wens')
    Radiobutton(lls_tmp_frame, text='OS', anchor='w', variable=value, value='OS').grid(row=0, column=1, padx=5, sticky='we')
    Radiobutton(lls_tmp_frame, text='UEFI SHELL', anchor='w', variable=value, value='UEFI SHELL').grid(row=1,column=1, padx=5, sticky='we')

    add_step = Button(lls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(lls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='we')


def check_power_state(frame, text):
    lls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        state = value.get()
        if state:
            text.insert(INSERT, f'{setting.vldata.OP_CHECK_POWER_STATE}: {state}\n')

    value = StringVar()
    value.set('S0')
    Label(lls_tmp_frame, text='Power', anchor='w', width=4).grid(row=0, column=0, rowspan=3, padx=5,
                                                                       sticky='wens')
    Radiobutton(lls_tmp_frame, text='S0', anchor='w', variable=value, value='S0').grid(row=0, column=1, padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='S5', anchor='w', variable=value, value='S5').grid(row=1, column=1,
                                                                                                       padx=5,
                                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='G3', anchor='w', variable=value, value='G3').grid(row=2, column=1,
                                                                                                       padx=5,
                                                                                                       sticky='we')

    add_step = Button(lls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(lls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=4, column=0, columnspan=2,
    #                                                                                     padx=5, pady=5, sticky='we')


def wait_for(frame, text):
    lls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        state = value.get()
        if state:
            text.insert(INSERT, f'{setting.vldata.OP_WAIT_FOR}: {state}\n')

    value = StringVar()
    value.set('S0')
    Label(lls_tmp_frame, text='State', anchor='w', width=4).grid(row=0, column=0, rowspan=4, padx=5,
                                                                       sticky='wens')
    Radiobutton(lls_tmp_frame, text='S0', anchor='w', variable=value, value='S0').grid(row=0, column=1, padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='S5', anchor='w', variable=value, value='S5').grid(row=1, column=1,
                                                                                       padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='OS', anchor='w', variable=value, value='OS').grid(row=2, column=1,
                                                                                       padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='UEFI SHELL', anchor='w', variable=value, value='UEFI SHELL').grid(row=3, column=1,
                                                                                       padx=5,
                                                                                       sticky='we')

    add_step = Button(lls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(lls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=5, column=0, columnspan=2,
    #                                                                                     padx=5, pady=5, sticky='we')


def switch_ac(frame, text):
    lls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        state = value.get()
        if state:
            text.insert(INSERT, f'{setting.vldata.OP_AC}: {state}\n')

    value = StringVar()
    value.set('On')
    Label(lls_tmp_frame, text='AC Operation', anchor='w', width=4).grid(row=0, column=0, rowspan=2, padx=5,
                                                                       sticky='wens')
    Radiobutton(lls_tmp_frame, text='On', anchor='w', variable=value, value='On').grid(row=0, column=1, padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='Off', anchor='w', variable=value, value='Off').grid(row=1, column=1,
                                                                                                       padx=5,
                                                                                                       sticky='we')

    add_step = Button(lls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(lls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=3, column=0, columnspan=2,
    #                                                                                     padx=5, pady=5, sticky='we')


def switch_dc(frame, text):
    lls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        state = value.get()
        if state:
            text.insert(INSERT, f'{setting.vldata.OP_DC}: {state}\n')

    value = StringVar()
    value.set('On')
    Label(lls_tmp_frame, text='DC Operation', anchor='w', width=4).grid(row=0, column=0, rowspan=2, padx=5,
                                                                        sticky='wens')
    Radiobutton(lls_tmp_frame, text='On', anchor='w', variable=value, value='On').grid(row=0, column=1, padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='Off', anchor='w', variable=value, value='Off').grid(row=1, column=1,
                                                                                         padx=5,
                                                                                         sticky='we')

    add_step = Button(lls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(lls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=3, column=0, columnspan=2,
    #                                                                                     padx=5, pady=5, sticky='we')


def reset(frame, text):
    lls_tmp_frame = __new_tmp_frame(frame)

    def __add_step(text, value):
        type = value.get()
        if type:
            text.insert(INSERT, f'{setting.vldata.OP_RESET}: {type}\n')

    value = StringVar()
    value.set('ANY')
    Label(lls_tmp_frame, text='Reset Types', anchor='w', width=4).grid(row=0, column=0, rowspan=3, padx=5,
                                                                 sticky='wens')
    Radiobutton(lls_tmp_frame, text='ANY', anchor='w', variable=value, value='ANY').grid(row=0, column=1, padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='WARM', anchor='w', variable=value, value='WARM').grid(row=1, column=1,
                                                                                       padx=5,
                                                                                       sticky='we')
    Radiobutton(lls_tmp_frame, text='COLD', anchor='w', variable=value, value='COLD').grid(row=2, column=1,
                                                                                       padx=5,
                                                                                       sticky='we')

    add_step = Button(lls_tmp_frame, text='Add Step', width=40, command=partial(__add_step, text, value))
    add_step.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='we')

    # semantics = 'Semantics:\n\nboot up system to specific environment, \ngenerally this should be the first validation step'
    # Label(lls_tmp_frame, text=semantics, background='lightyellow', justify='left').grid(row=4, column=0, columnspan=2,
    #                                                                                     padx=5, pady=5, sticky='we')



