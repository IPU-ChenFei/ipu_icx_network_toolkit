#!/usr/bin/env python

from src.dpmo.tests.case_base import *
import sys

class PowerCyclingS3General(TestBase):
    # Flow: S3 -> DC ON -> OS/UEFI -> Sleep -> S3 -> ...
    def __init__(self):
        super().__init__()
        self.test_cls = 'S3General'


def main():
    cycle = PowerCyclingS3General()
    result = cycle.test_entry()
    sys.exit(result)