#!/usr/bin/env python

from queue import Queue


def singleton(cls):
    _instance = {}
    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return _singleton


class Event:
    # Event with state
    SUT_IN_G3 = 'G3'
    SUT_IN_S5 = 'S5'
    SUT_IN_S4 = 'S4'
    SUT_IN_S3 = 'S3'
    SUT_IN_S0 = 'S0'
    SUT_IN_OS = 'OS'
    SUT_IN_UEFI = 'UEFI'

    # Event with errors
    SUT_IN_TIMEOUT = 'TIMEOUT'

    SUT_IN_AUTO_SLEEP = 'S0S3'
    SUT_IN_AUTO_HIBERNATE = 'S0S4'
    SUT_IN_AUTO_SHUTDOWN = 'S0S5'
    SUT_IN_AUTO_RESET_S3 = 'S0S3S0'
    SUT_IN_AUTO_RESET_S4 = 'S0S4S0'
    SUT_IN_AUTO_RESET_S5 = 'S0S5S0'


@singleton
class EventQueue:
    # Event queue
    def __init__(self):
        self.__event_queue = Queue()

    def get_event(self):
        return self.__event_queue.get()

    def put_event(self, value):
        self.__event_queue.put(value)


