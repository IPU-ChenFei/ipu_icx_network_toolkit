#!/usr/bin/env python

import threading
import time

from src.dpmo.lib.config import *
from src.dpmo.lib.event import *
from dtaf_core.lib.tklib.basic.log import logger


class MonitorService(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.event_queue = EventQueue()
        self.is_stop = False
        self.__start_monitor = True
        self.__start_time = time.time()

    @property
    def start_time(self):
        return self.__start_time

    @start_time.setter
    def start_time(self, value):
        self.__start_time = value

    @property
    def start_monitor(self):
        return self.__start_monitor

    @start_monitor.setter
    def start_monitor(self, value):
        self.__start_monitor = value

    def stop(self):
        logger.info('stop monitor service ...')
        self.is_stop = True
        self.join(60)
        if self.is_alive():
            self.stop()

    def run(self):
        logger.info('monitor service is running ...')
        while not self.is_stop:
            # cycle timeout monitor
            if self.start_monitor:
                now = time.time()
                if now - self.start_time > DpmoCfg.one_cycle_max_time:
                    self.start_monitor = False
                    self.event_queue.put_event(Event.SUT_IN_TIMEOUT)
