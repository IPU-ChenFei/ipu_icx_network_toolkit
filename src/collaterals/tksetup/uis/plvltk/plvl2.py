#!/usr/bin/env python

from tkinter import *
from tkinter import ttk
from functools import partial

import highlevel_step
import lowlevel_step
import bios_log
import generated_step
import dryrun_log
import system_monitor
import setting
import tool
import cbox
import help
import utils
import record
import executor


print(f'TkVersion: {TkVersion}')


"""
==> Main Window
"""
window = Tk()
window.title('PLVL (Platform Level Validation Language ~ High Level Step Dryrun)')
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window_width = int(screen_width * 0.5)
window_height = int(screen_height * 0.8)
# window.geometry(f'{window_width}x{window_height}+0+0')
window.geometry(f'1565x885+0+0')
window.resizable(width=True, height=True)
window.maxsize(width=1565, height=885)


"""
==>  Menu Bar
"""
menubar = Menu(window)

# file menu
# file_menu = Menu(menubar, tearoff=0)
# file_menu.add_command(label='Open File')
# file_menu.add_command(label='Exit', command=window.destroy)
# menubar.add_cascade(label='File', menu=file_menu)

# sub menu
# find_menu = Menu(file_menu, tearoff=0)
# find_menu.add_command(label='Find Next')
# find_menu.add_command(label='Find Pre')
# file_menu.add_cascade(label='Find', menu=find_menu)

# setting menu
setting_menu = Menu(menubar, tearoff=0)
setting_menu.add_command(label='SUT', command=setting.set_sut)
setting_menu.add_command(label='Feature', command=setting.set_feature)
# setting_menu.add_command(label='Debug', command=setting.set_debug)
setting_menu.add_command(label='Tool', command=setting.set_tool)
menubar.add_cascade(label='Setting', menu=setting_menu)

# tool menu
tool_menu = Menu(menubar, tearoff=0)
tool_menu.add_command(label='File Transfer', command=tool.file_transfer)
tool_menu.add_command(label='Utility Setup')
menubar.add_cascade(label='Tool', menu=tool_menu)

# # record menu
# tool_menu = Menu(menubar, tearoff=0)
# tool_menu.add_command(label='Start', command=record.start)
# tool_menu.add_command(label='Stop', command=record.stop)
# menubar.add_cascade(label='Record', menu=tool_menu)
#
# tool_menu = Menu(menubar, tearoff=0)
# tool_menu.add_command(label='Schedule Task', command=record.start)
# tool_menu.add_command(label='Find Log', command=record.stop)
# menubar.add_cascade(label='Executor', menu=tool_menu)
#
# # cbox menu
# cbox_menu = Menu(menubar, tearoff=0)
# cbox_menu.add_command(label='Soundwave', command=cbox.soundwave)
# menubar.add_cascade(label='Cbox', menu=cbox_menu)

# help menu
help_menu = Menu(menubar, tearoff=0)
help_menu.add_command(label='HLS Wiki', command=help.hls_wiki)
help_menu.add_command(label='Toolkit Wiki', command=help.toolkit_wiki)
help_menu.add_command(label='About', command=help.about)
menubar.add_cascade(label='Help', menu=help_menu)

window.config(menu=menubar)

# popup menu
popup_menu = Menu(window, tearoff=False)


"""
Window Container
"""
container = Canvas(window)
scrollable_frame = Frame(window)
scrollable_frame.bind(
    '<Configure>',
    lambda e: container.configure(
        scrollregion=container.bbox("all")
    )
)
container.create_window(0, 0, window=scrollable_frame, anchor='nw')
scrollbar_x = Scrollbar(window, orient='horizontal', command=container.xview)
scrollbar_v = Scrollbar(window, orient='vertical', command=container.yview)
container.configure(xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_v.set)
scrollbar_v.pack(side='right', fill='y')
scrollbar_x.pack(side='bottom', fill='x')
container.pack(fill='both', expand=True)


"""
==> Frame Layout Definition
--------------------------------------------------
High Level Step | DryRun Log     | BIOS Log
--------------------------------------------------
Low  Level Step | Generated Step | System Monitor
--------------------------------------------------
"""
hls_frame = LabelFrame(scrollable_frame, text='High Level Step', pady=10, font=utils.TITLE_FONT)
lls_frame = LabelFrame(scrollable_frame, text='Low Level Step', pady=10, font=utils.TITLE_FONT)
dlog_frame = LabelFrame(scrollable_frame, text='DryRun Log', pady=10, font=utils.TITLE_FONT)
step_frame = LabelFrame(scrollable_frame, text='Generated Step', pady=10, font=utils.TITLE_FONT)
blog_frame = LabelFrame(scrollable_frame, text='BIOS Log', pady=10, font=utils.TITLE_FONT)
monitor_frame = LabelFrame(scrollable_frame, text='System Monitor', pady=10, font=utils.TITLE_FONT)

hls_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nwes')
lls_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nwes')
dlog_frame.grid(row=0, column=1, padx=0, pady=10, sticky='nwes')
step_frame.grid(row=1, column=1, padx=0, pady=10, sticky='nwes')
blog_frame.grid(row=0, column=2, padx=10, pady=10, sticky='nwes')
monitor_frame.grid(row=1, column=2, padx=10, pady=10, sticky='nwes')


# dryrun log layout
scroll_v = Scrollbar(dlog_frame)
scroll_v.pack(side='right', fill='y')
dlog_output = utils.TextMonitor(dlog_frame, width=60, height=20, foreground='white', background='black', insertbackground='white')
dlog_output.pack(fill='both', padx=5)
dlog_output.config(yscrollcommand=scroll_v.set)
scroll_v.config(command=dlog_output.yview)

# pop up menu
dlog_output.bind('<Button-3>', lambda event: utils.TextPopup.right_click(popup_menu, dlog_output, event))


# generated step layout
scroll_v = Scrollbar(step_frame)
scroll_v.pack(side='right', fill='y')
step_output = utils.TextMonitor(step_frame, width=60, height=25)
step_output.pack(fill='both', padx=5)
step_output.config(yscrollcommand=scroll_v.set)
scroll_v.config(command=step_output.yview)

# pop up menu
step_output.bind('<Button-3>', lambda event: utils.TextPopup.right_click(popup_menu, step_output, event))


# high level step layout
hls_func_frame = Frame(hls_frame)
hls_tmp_frame = Frame(hls_frame, width=300, height=320, bg='lightblue')

hls_func_frame.grid(row=0, column=0, sticky='nwes')
hls_tmp_frame.grid(row=0, column=1, sticky='nwes', padx=5)

hls_boot_to = Button(hls_func_frame, text='Boot to', anchor='w', width=20, command=partial(highlevel_step.boot_to, hls_frame, step_output)).pack(fill='both', padx=5)
hls_reset_to = Button(hls_func_frame, text='Reset to', anchor='w', command=partial(highlevel_step.reset_to, hls_frame, step_output)).pack(fill='both', padx=5)
hls_set_feature = Button(hls_func_frame, text='Set Feature', anchor='w', command=partial(highlevel_step.set_feature, hls_frame, step_output)).pack(fill='both', padx=5)
hls_run_tcd_block = Button(hls_func_frame, text='Run TCD Block', anchor='w', command=partial(highlevel_step.run_tcd_block, hls_frame, step_output)).pack(fill='both', padx=5)
hls_execute_itp_command = Button(hls_func_frame, text='Execute ITP Command', anchor='w', command=partial(highlevel_step.execute_itp_command, hls_frame, step_output)).pack(fill='both', padx=5)
hls_execute_host_command = Button(hls_func_frame, text='Execute Host Command', anchor='w', command=partial(highlevel_step.execute_host_command, hls_frame, step_output)).pack(fill='both', padx=5)
hls_execute_command = Button(hls_func_frame, text='Execute Command', anchor='w', command=partial(highlevel_step.execute_command, hls_frame, step_output)).pack(fill='both', padx=5)
hls_wait = Button(hls_func_frame, text='Wait', anchor='w', command=partial(highlevel_step.wait, hls_frame, step_output)).pack(fill='both', padx=5)
hls_clear_cmos = Button(hls_func_frame, text='Clear CMOS', anchor='w', command=partial(highlevel_step.clear_cmos, hls_frame, step_output)).pack(fill='both', padx=5)


# low level step layout
lls_func_frame = Frame(lls_frame)
lls_tmp_frame = Frame(lls_frame, width=300, height=415, bg='lightblue')

lls_func_frame.grid(row=0, column=0, sticky='nwes')
lls_tmp_frame.grid(row=0, column=1, sticky='nwes', padx=5)

# lls_prepare = Button(lls_func_frame, text='PREPARE', anchor='w').pack(fill='both', padx=5)
# lls_step = Button(lls_func_frame, text='STEP', anchor='w', command=partial(lowlevel_step.step, lls_frame, step_output)).pack(fill='both', padx=5)
lls_check_environment = Button(lls_func_frame, text='Check Environment', anchor='w', width=20, command=partial(lowlevel_step.check_environment, lls_frame, step_output)).pack(fill='both', padx=5)
lls_check_power_state = Button(lls_func_frame, text='Check Power State', anchor='w', command=partial(lowlevel_step.check_power_state, lls_frame, step_output)).pack(fill='both', padx=5)
# lls_execute_command = Button(lls_func_frame, text='Execute Command', anchor='w').pack(fill='both', padx=5)
# lls_execute_host_command = Button(lls_func_frame, text='Execute Host Command', anchor='w').pack(fill='both', padx=5)
# lls_execute_itp_command = Button(lls_func_frame, text='Execute ITP Command', anchor='w').pack(fill='both', padx=5)
# lls_wait = Button(lls_func_frame, text='Wait', anchor='w').pack(fill='both', padx=5)
lls_wait_for = Button(lls_func_frame, text='Wait For', anchor='w', command=partial(lowlevel_step.wait_for, lls_frame, step_output)).pack(fill='both', padx=5)
# lls_clear_cmos = Button(lls_func_frame, text='Clear CMOS', anchor='w').pack(fill='both', padx=5)
lls_switch_ac = Button(lls_func_frame, text='Switch AC', anchor='w', command=partial(lowlevel_step.switch_ac, lls_frame, step_output)).pack(fill='both', padx=5)
lls_switch_dc = Button(lls_func_frame, text='Switch DC', anchor='w', command=partial(lowlevel_step.switch_dc, lls_frame, step_output)).pack(fill='both', padx=5)
lls_reset = Button(lls_func_frame, text='Reset', anchor='w', command=partial(lowlevel_step.reset, lls_frame, step_output)).pack(fill='both', padx=5)
# lls_set_bios_knob = Button(lls_func_frame, text='Set BIOS Knob', anchor='w').pack(fill='both', padx=5)
# lls_repeat = Button(lls_func_frame, text='Repeat', anchor='w').pack(fill='both', padx=5)
# lls_log = Button(lls_func_frame, text='Log', anchor='w').pack(fill='both', padx=5)


# bios log layout
scroll_v = Scrollbar(blog_frame)
scroll_v.pack(side='right', fill='y')
bios_output = utils.TextMonitor(blog_frame, width=60, height=20)
bios_output.pack(fill='both', padx=5)
bios_output.config(yscrollcommand=scroll_v.set)
scroll_v.config(command=bios_output.yview)

# pop up menu
bios_output.bind('<Button-3>', lambda event: utils.TextPopup.bios_right_click(popup_menu, bios_output, event))


# system monitor layout
PIXEL_IMAGE = PhotoImage(width=1, height=1)
power_state_label = Label(monitor_frame, image=PIXEL_IMAGE, compound='center', text='S0', width=80, height=80, bg='#E8C5B6', font=utils.HIGHLIGHT_FONT)
start_power_state = Button(monitor_frame, image=PIXEL_IMAGE, compound='center', text='START', bg='green', command=partial(system_monitor.start_power_state_detect, power_state_label), width=80, height=33, justify='left', font=utils.STRONG_FONT)
stop_power_state = Button(monitor_frame, image=PIXEL_IMAGE, compound='center', text='STOP', bg='red', command=partial(system_monitor.stop_power_state_detect, power_state_label), width=80, height=33, justify='left', font=utils.STRONG_FONT)
post_code_label = Label(monitor_frame, image=PIXEL_IMAGE, compound='center',text='00', width=80, height=80, bg='#E8C5B6', font=utils.HIGHLIGHT_FONT)
start_post_code = Button(monitor_frame, image=PIXEL_IMAGE, compound='center', text='START', bg='green', command=partial(system_monitor.start_post_code_detect, post_code_label), width=80, height=33, justify='left', font=utils.STRONG_FONT)
stop_post_code = Button(monitor_frame, image=PIXEL_IMAGE, compound='center', text='STOP', bg='red', command=partial(system_monitor.stop_post_code_detect, post_code_label), width=80, height=33, justify='left', font=utils.STRONG_FONT)

start_power_state.grid(row=0, column=0, padx=5)
stop_power_state.grid(row=1, column=0, pady=2)
power_state_label.grid(row=0, column=1, rowspan=2, pady=2)
start_post_code.grid(row=2, column=0)
stop_post_code.grid(row=3, column=0, pady=2)
post_code_label.grid(row=2, column=1, rowspan=2, pady=2)

utils.ToolTip(power_state_label, 'power state monitor')
utils.ToolTip(post_code_label, 'post code monitor')


# start loop
window.mainloop()