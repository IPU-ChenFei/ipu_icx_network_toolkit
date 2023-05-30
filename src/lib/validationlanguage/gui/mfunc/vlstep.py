#!/usr/bin/env python
# -*- coding: utf-8 -*-
import wx
from threading import Thread, Event
from time import sleep
from dtaf_core.lib.tklib.basic.const import *
from dtaf_core.lib.tklib.basic.testcase import *
from src.lib.validationlanguage.src_translator.const import *

from src.lib.validationlanguage.gui.mfunc.utils import VlTestCase


class VlSteps(Thread):
    def __init__(self, textbox, logtextbox, biostextbox, _globals, _locals) -> None:
        self.hlsteptext = textbox
        self.dryrunlog = logtextbox
        self.vltc = VlTestCase(self.dryrunlog, biostextbox, _globals, _locals)
        self.steps_queue = []
        Thread.__init__(self)
        self.stop_event = Event()
        self.stop_event.clear()
        self.start()

    def run(self) -> None:
        while True:
            if self.stop_event.is_set():
                break
            if len(self.steps_queue) == 0:
                sleep(1)
                continue

            stime = datetime.datetime.now()
            try:
                step = self.steps_queue.pop(0)
                self.dryrunlog.AppendText(f'''\n>>>> ++++++++++ START STEP '{step}' AT {stime} ++++++++++\n''')
                self.vltc.execute_high_level(step)
            except Exception as e:
                self.dryrunlog.AppendText(f'\n{e}\n')
            etime = datetime.datetime.now()
            self.dryrunlog.AppendText(f'\n<<<<++++++++++ STEP END AT {etime}, time duration {etime - stime} ++++++++++\n')

    def stop(self):
        self.stop_event.set()

    def addstep(self, step):
        self.hlsteptext.AppendText(f'{step}\n')
        self.steps_queue.append(step)

    def toggle_bios_log(self, on = True):
        self.vltc.toggle_bios_log(on)

    def boot_to(self, target):
        step = f'{OP_BOOT_TO}: {target}'
        self.addstep(step)

    def reset_to(self, target):
        step = f'{OP_RESET_TO}: {target}'
        self.addstep(step)

    def set_feature(self, features):
        step = f'{OP_SET_FEATURE}: {features}'
        self.addstep(step)

    def run_tcd_block(self, tcd, repeat):
        step = f'{OP_TCDB}: {tcd}'
        if repeat is not None:
            step += f', repeat={repeat}'
        self.addstep(step)

    def execute_commmand(self, cmd, timeout = None, no_check = False):
        step = f'{OP_EXECUTE_CMD}: '
        if timeout is not None:
            step += f'timeout={timeout}, '
        if no_check:
            step += f'nocheck, '
        step += f'{cmd}'
        self.addstep(step)

    def execute_itp_command(self, cmd, itplib):
        step = f'{OP_ITP_CMD}: {cmd}'
        if self.vltc.itplib != itplib:
            self.vltc.itplib = itplib
        self.addstep(step)

    def execute_host_command(self, cmd, timeout = None, no_check = False):
        step = f'{OP_EXECUTE_HOST_CMD}: '
        if timeout is not None:
            step += f'timeout={timeout}, '
        if no_check:
            step += f'nocheck, '
        step += f'{cmd}'
        self.addstep(step)

    def hlwait(self, seconds):
        step = f'{OP_WAIT}: {seconds}'
        self.addstep(step)

    def hlclearcmos(self):
        step = f'Clear CMOS:'
        self.addstep(step)

    def ac(self, action):
        step = f'{OP_AC}: {action}'
        self.addstep(step)

    def dc(self, action):
        step = f'{OP_DC}: {action}'
        self.addstep(step)

    def reset(self, method):
        step = f'{OP_RESET}: {method}'
        self.addstep(step)

    def wait_for(self, state):
        step = f'{OP_WAIT_FOR}: {state}'
        self.addstep(step)

    def check_envirnment(self, env):
        step = f'{OP_CHECK_ENVIRONMENT}: {env}'
        self.addstep(step)

    def check_power(self, state):
        step = f'{OP_CHECK_POWER_STATE}: {state}'
        self.addstep(step)
