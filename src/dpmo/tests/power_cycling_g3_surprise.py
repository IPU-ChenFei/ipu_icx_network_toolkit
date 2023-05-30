#!/usr/bin/env python

from src.dpmo.tests.case_base import *
import sys

class PowerCyclingG3Surprise(TestBase):
    # Flow: G3 -> AC ON -> OS/UEFI -> AC OFF -> G3 -> ...
    def __init__(self):
        super().__init__()
        self.test_cls = 'G3Surprise'


def main():
    cycle = PowerCyclingG3Surprise()
    result = cycle.test_entry()
    sys.exit(result)

if __name__ == '__main__':
    main()