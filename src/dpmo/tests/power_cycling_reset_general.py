#!/usr/bin/env python

from src.dpmo.tests.case_base import *
import sys

class PowerCyclingResetGeneral(TestBase):
    # Flow: OS/UEFI -> Reset -> OS/UEFI -> ...
    def __init__(self):
        super().__init__()
        self.test_cls = 'ResetGeneral'


def main():
    cycle = PowerCyclingResetGeneral()
    result = cycle.test_entry()
    sys.exit(result)
if __name__ == '__main__':
    main()