#!/usr/bin/env python

from prettytable import PrettyTable

from src.dpmo.lib.test_scenario import get_report_dict
# from .config import *
from dtaf_core.lib.tklib.basic.log import logger


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


@singleton
class TestReport:
    # todo: generate single instance table for recording all absornal cycles (at most show 5 cycles at a cell, hide other cycles if any)
    # todo: all other modules will fill data to it
    """
    demo internal table structure
    ---------------------------------------------------------------------------
    checker name             | cycles / ?
    ---------------------------------------------------------------------------
    check_linux_syslog_error | 1, 3, 5 / 2 4 6
    ---------------------------------------------------------------------------
    check_linux_system_cfg   | 2, 4, 6
    ---------------------------------------------------------------------------
    check_bios_mcerr         |
    ---------------------------------------------------------------------------
    ...                      |
    ---------------------------------------------------------------------------
    """

    def __init__(self):
        self.checker_record = get_report_dict()

    def generate_table(self):
        # checker_record = {
        #     'a': [],
        #     "b": [1, 2],
        #     "c": [i for i in range(1, 13)]
        # }
        # todo: generate real table, as some data need to be calculated between cycles
        tb = PrettyTable()
        tb.field_names = ["Checker Name", "Cycles"]
        tb.align = "l"
        # fd_name = ["Checker Name", "Cycles"]
        # cell = 1
        # for value in checker_record.values():
        #     if len(value) > 5:
        #         cell = len(value) // 5 + 1
        #         for i in range(cell - 1):
        #             fd_name.append("")
        # tb.field_names = fd_name
        # print(tb.field_names)
        if self.checker_record:
            for item, val in self.checker_record.items():
                tb.add_row([item, str(val).strip('[]')])
            #     if not val:
            #         continue
            #     else:
            #         if len(val) <= 5:
            #             tb.add_row([item, val])
            #         else:
            #             # val: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            #             # cell: 3
            #             cell = len(val) // 5 + 1
            #             for i in range(cell - 2):
            #                 tb.field_names.append("")
            #             row_list = [item]
            #             for i in range(cell):
            #                 row_list.append(val[0:5])
            #                 print(f'row list: {row_list}')
            #                 val = val[5:]
            #                 print(f'left item: {val}')
            #             tb.add_row(row_list)
            return tb

    def print_table(self):
        table = self.generate_table()
        logger.info('========== DPMO Cycling Test Report ==========')
        print(table)
        # todo: print table in log file, without timestamp ahead of table rows

#
# if __name__ == '__main__':
#     TestReport().print_table()
