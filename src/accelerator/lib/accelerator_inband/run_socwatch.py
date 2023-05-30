import sys
import argparse
import time
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger
from check_error import check_error


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run socwatch tool'
                    '--log_num <execute number>')
    parser.add_argument('-l', '--log_num', required=True, dest='log_num', action='store', help='execute number')
    ret = parser.parse_args(args)
    return ret


def __get_core_num():
    """
          Purpose: Get current SUT core numbers
          Args:
              No
          Returns:
              Yes: return core numbers
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Get current SUT core numbers
                    __get_core_num()
    """
    _, out, err = lnx_exec_command('lscpu', timeout=60)
    line_list = out.strip().split('\n')
    for line in line_list:
        word_list = line.split()
        if word_list[0] == 'Core(s)':
            core_num = int(word_list[3])
            return core_num


def __get_thread_num():
    """
          Purpose: Get current SUT core numbers
          Args:
              No
          Returns:
              Yes: return core numbers
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Get current SUT core numbers
                    __get_core_num()
    """
    _, out, err = lnx_exec_command('lscpu', timeout=60)
    line_list = out.strip().split('\n')
    for line in line_list:
        word_list = line.split()
        if word_list[0] == 'CPU(s):':
            thread_num = int(word_list[1])
            return thread_num


def __cc6_value_check(out):
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    core_num = __get_core_num()
    line_list = out.strip().split('CC6')
    cc6_line_list = line_list[1].split('Core C-State Summary: Entry Counts')
    word_list = cc6_line_list[0].strip().split(',')
    value_list = []
    for word in word_list:
        value_list.append(word.strip())
    less_100_value_list = []
    for word in value_list:
        if word != '' and float(word) <= 100.00:
            less_100_value_list.append(word)
    cc6_num = 0
    for word in less_100_value_list:
        if float(word) >= 70:
            cc6_num += 1
    if cc6_num != cpu_num * core_num:
        logger.error('Not all core CC6 Residency value more than 70%')
        raise Exception('Not all core CC6 Residency value more than 70%')


def __cpu_idle_value_check(out):
    thread_num = __get_thread_num()
    line_list = out.strip().split('CPU Idle')
    cpu_idle_list = line_list[1].split('CPU P-State/Frequency Summary: Total Samples Received')
    cpu_idle_list = cpu_idle_list[0].strip().split(',')
    word_list = []
    for word in cpu_idle_list:
        word_list.append(word.strip())
    print(word_list)
    cpu_idle_value_less_100_list = []
    for word in word_list:
        if word != '' and float(word) <= 100.00:
            cpu_idle_value_less_100_list.append(word)
    cpu_idle_num = 0
    for word in cpu_idle_value_less_100_list:
        if float(word) >= 70:
            cpu_idle_num += 1
    if cpu_idle_num != thread_num:
        logger.error('Not all thread cpu idle value more than 70%')
        raise Exception('Not all thread cpu idle value more than 70%')


def copy_socwatch_script():
    lnx_exec_command(f'cp -r {PPEXPECT_NAME} {PPEXPECT_SOCWATCH_PATH_L}')
    lnx_exec_command(f'cp -r {SOCWATCH_SCRIPT_NAME} {SOCWATCH_SCRIPT_PATH_L}')


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ll', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def run_socwatch(log_num):
    """
          Purpose: Run socwatch tool
          Args:
              Yes: log_num is which time run socwatch tool.
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run socwatch tool
                  install_socwatch()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    copy_socwatch_script()
    folder_name = get_folder_name(SOCWATCH_PATH_L)
    ret, out, err = lnx_exec_command(f'python3 socwatch.py run_socwatch', timeout=10*60, cwd=SOCWATCH_SCRIPT_PATH_L)
    check_error(err)
    lnx_exec_command(f'rm -rf /root/socwatch{log_num}*.log')
    lnx_exec_command(f'mv /root/socwatch.log /root/socwatch{log_num}-{current_time}.log', timeout=10*60)
    lnx_exec_command(f'cp /root/socwatch{log_num}*.log {LOGS_L}')
    lnx_exec_command(f'rm -rf /root/runsocwatch{log_num}*.log')
    lnx_exec_command(
        f'mv {SOCWATCH_PATH_L}{folder_name}/runsocwatch.log /root/runsocwatch{log_num}-{current_time}.log',
        timeout=10 * 60)
    lnx_exec_command(f'cp /root/runsocwatch{log_num}*.log {LOGS_L}')
    lnx_exec_command(f'rm -rf /root/SoCWatchOutput{log_num}*.csv')
    lnx_exec_command(
        f'mv {SOCWATCH_PATH_L}{folder_name}/SoCWatchOutput.csv /root/SoCWatchOutput{log_num}-{current_time}.csv',
        timeout=10 * 60)
    lnx_exec_command(f'cp /root/SoCWatchOutput{log_num}*.log {LOGS_L}')
    _, out, err = lnx_exec_command(f'cat SoCWatchOutput{log_num}*.csv', timeout=60, cwd='/root')
    __cc6_value_check(out)
    __cpu_idle_value_check(out)


if __name__ == '__main__':
    args_parse = setup_argparse()
    run_socwatch(args_parse.log_num)

