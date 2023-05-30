#!/usr/bin/env python

from src.dpmo.tests.case_base import *
import sys

class PowerCyclingUefi2OsReset(TestBase):
    # Flow: OS -> Reset -> UEFI -> Continue -> OS -> ...
    def __init__(self):
        super().__init__()
        self.test_cls = 'Uefi2OsReset'


def main():
    cycle = PowerCyclingUefi2OsReset()
    result = cycle.test_entry()
    sys.exit(result)

if __name__ == '__main__':
    main()