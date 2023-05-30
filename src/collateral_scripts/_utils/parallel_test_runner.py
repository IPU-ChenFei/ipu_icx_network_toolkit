#!/usr/bin/env python

import argparse
import copy
import os
import time
import subprocess
import warnings
import multiprocessing as mp

from configparser import ConfigParser


class ModifiedParser(ConfigParser):
    def __init__(self):
        super().__init__(allow_no_value=True, delimiters=(' ',))

    def optionxform(self, optionstr):
        return optionstr

    def parser(self):
        assert (isinstance(self, ConfigParser))
        d = {}
        for sec in self.sections():
            d2 = {}
            for op in self.options(sec):
                d2[op] = self.get(sec, op)
            d[sec] = copy.deepcopy(d2)
        return d


TEST_POOL = {}


parser = argparse.ArgumentParser()
parser.add_argument('--number', help='Test numbers running in parallel, >=1', type=int)
parser.add_argument('--sequence', help='Test sequence absolute path: e.g., testplan.ini')
parser.add_argument('--domain', help='Test domain absolute path')
parser.add_argument('--target', help='Test OS section name in testplan.ini')
args = parser.parse_args()

number = args.number
sequence = args.sequence
domain = args.domain
target = args.target

if number > mp.cpu_count():
    warnings.warn('Task Numbers (>) Logical Processors')

config = ModifiedParser()
config.read(sequence)
plan = config.parser()
print(plan)


if target not in plan.keys():
    raise RuntimeError(f'{target} not found in {sequence}')
else:
    tests = plan[f'{target}']
    for test, parameter in tests.items():
        TEST_POOL.update({test: 'Python ' + os.path.join(domain, test) + ' ' + parameter})


def run_cmd(number, **kwargs):
    """
    Executing multiple commands in parallel

    :param kwargs: commands keyword parameters, just like: cmd1='dir c:\\', cmd2='dir C:\\Python39444'
    :return: Result dict including error code and command output, just like below format:
            {
                'cmd2': {
                    'ret': 1,
                    'out': 'error messages'
                },
                'cmd01: {
                    'ret': 0,
                    'out': 'command results'
                }
            }
    """

    print(rf"""
    
======================================================================================================
<<Function for running x{number} tasks In Parallel>>

Report will be recorded in: 
    {os.path.dirname(__file__)}\report.txt

Demo Usage:
    Python parallel_test_runner.py 
        --number=4 
        --sequence=C:\xijun-dev\private-fork\frameworks.automation.dtaf.content.egs.dtaf-content-egs\automation_testcases\pm_bhs_simics.ini 
        --domain=C:\xijun-dev\private-fork\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\power_management\tests 
        --target=CentOS

Schedule Tasks: 
    {kwargs.values()}
======================================================================================================
    """)

    report = open('report.txt', 'wb')

    procs = {}
    results = {}

    added = []
    executing = []
    remaining = list(kwargs.keys())

    while True:
        for c in remaining:
            if c not in added and len(executing) < number:
                procs[c] = subprocess.Popen(
                    kwargs[c],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True
                )
                added.append(c)
                executing.append(c)
                remaining.remove(c)
                time.sleep(3)
                print(f'Executing: {c} {kwargs[c]}')
                continue
            else:
                break

        if len(executing) < number and remaining:
            continue

        if len(executing) == 0:
            break

        for e in executing:
            proc = procs[e]
            ret = proc.poll()

            if ret is None:
                continue

            print(f'Running List: {executing}')

            executing.remove(e)
            output = proc.stdout.read().decode()
            results[e] = {
                'ret': ret,
                'out': output
            }

            # log result to file
            label = 'PASS' if ret == 0 else 'FAIL'
            report.write(f'{e}: {label}\n'.encode())
            report.flush()

    return results


if __name__ == '__main__':
    # faketests = {}
    #
    # for dirpath, dirnames, filenames in os.walk(r'C:\Users\xijunli\PycharmProjects\tmp\faketests'):
    #     for f in filenames:
    #         if f.endswith('.py'):
    #             fn = os.path.join(dirpath, f)
    #             print(fn)
    #             faketests.update({f: 'python '+fn})
    #
    # run_cmd(number, **faketests)

    # run_cmd(4, CMD1='dir c:\\', CMD2='dir C:\\Python39444', CMD3='dir c:\\', CMD4='dir C:\\Python39444', CMD5='dir c:\\', CMD6='dir C:\\Python39444')

    run_cmd(number, **TEST_POOL)