#!/usr/bin/env python

from src.dpmo.tests.case_base import *
import sys

class PowerCyclingS5General(TestBase):
    # Flow: S5 -> DC ON -> OS/UEFI -> Shutdown -> S5 -> ...
    def __init__(self):
        super().__init__()
        self.test_cls = 'S5General'


def main():
    cycle = PowerCyclingS5General()
    result = cycle.test_entry()
    sys.exit(result)

if __name__ == '__main__':
    main()