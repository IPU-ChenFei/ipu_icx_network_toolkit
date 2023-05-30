#!/usr/bin/env python


import logging
import os
import sys
import time


DEFAULT_LOG_PATH = os.path.join(os.path.dirname(sys.argv[0]), '_logs')
DEFAULT_LOG_NAME = os.path.basename(os.path.splitext(sys.argv[0])[0]) + time.strftime('-%Y%m%d%H%M%S')
DEFAULT_LOG_FILE = os.path.join(DEFAULT_LOG_PATH, DEFAULT_LOG_NAME)


def logger(logfile=None):
    if not logfile:
        logfile = DEFAULT_LOG_FILE

    logpath = os.path.dirname(logfile)
    logname = os.path.basename(logfile)

    if not os.path.exists(logpath):
        os.makedirs(logpath)

    log = logging.getLogger(logname)

    __formatter = logging.Formatter('[%(asctime)s -%(filename)s -%(funcName)s -LINE:%(lineno)s -%(levelname)s] %(message)s')
    __h_file = logging.FileHandler(logfile)
    __h_stream = logging.StreamHandler()
    __h_file.setFormatter(__formatter)
    __h_stream.setFormatter(__formatter)

    log.setLevel(logging.DEBUG)

    log.addHandler(__h_file)
    log.addHandler(__h_stream)

    return log


log = logger()