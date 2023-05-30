#!/usr/bin/env python
# -*- coding: utf-8 -*-
import wx
from threading import Thread, Event
from time import sleep
from dtaf_core.lib.tklib.infra.hwctrl.mix import MixHwtrl
from dtaf_core.lib.tklib.basic.const import SUT_STATUS

class VlMonitor(Thread):
    POWR_STATE = 'powerstate'
    POST_CODE = 'postcode'
    def __init__(self) -> None:
        super().__init__()
        self.stop_event = Event()
        self.stop_event.clear()
        self.monitors = {}
        self.start()
        self._hwctrl = None

    def _toggle_task(self, task_name, label=None):
        if not isinstance(task_name, str):
            return

        if task_name in self.monitors:
            self.monitors[task_name]['enable'] = not self.monitors[task_name]['enable']
            if label is not None:
                self.monitors[task_name]['label'] = label
        else:
            self.monitors[task_name] = {'enable': True, 'label': label}

    def toggle_power_state(self, label):
        self._toggle_task(self.POWR_STATE, label)

    def toggle_post_code(self, label):
        self._toggle_task(self.POST_CODE, label)

    def stop(self):
        self.stop_event.set()

    def run(self) -> None:
        while True:
            if self.stop_event.is_set():
                break

            for k in list(self.monitors.keys()):
                task = self.monitors[k]
                if not task:
                    continue

                if not task['enable']:
                    if task['label'] is not None:
                        task['label'].Clear()
                    continue

                if k == self.POWR_STATE:
                    s = self.hwctrl().get_power_state()
                    if s == SUT_STATUS.S0:
                        s = 'S0'
                    if 'label' in task and task['label'] is not None:
                        task['label'].SetValue(s)
                elif k == self.POST_CODE:
                    s = self.hwctrl().get_post_code()
                    s = 'None' if s is None else s
                    if 'label' in task and task['label'] is not None:
                        task['label'].SetValue(s)

            sleep(1)

    def hwctrl(self):
        if self._hwctrl is None:
            self._hwctrl = MixHwtrl()

        return self._hwctrl
