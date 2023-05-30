import sys
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger


def qat_service_stop_start():
    """
         Purpose: Check QAT service stop and QAT service start function
         Args:
             No
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: run qat_service stop and qat_service start
                   qat_service_stop_start()
   """
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    _, out, err = lnx_exec_command('service qat_service stop', timeout=10 * 60)
    line_list = out.strip().split('\n')
    dev_num = 0
    stopFlag = False
    for line in line_list:
        if 'Stopping device qat_dev' in line:
            dev_num += 1
        if 'Stopping all devices' in line:
            stopFlag = True
    if (dev_num != cpu_num * 16 * QAT_DEVICE_NUM) and (not stopFlag):
        logger.error('Not all QAT vf stopped')
        raise Exception('Not all QAT vf stopped')
    _, out, err = lnx_exec_command('service qat_service start', timeout=10 * 60)
    line_list = out.strip().split('\n')
    dev_num = 0
    for line in line_list:
        if 'state: up' in line:
            dev_num += 1
    if dev_num != cpu_num * QAT_DEVICE_NUM:
        logger.error('Not all QAT pf status show up')
        raise Exception('Not all QAT pf status show up')


if __name__ == '__main__':
    qat_service_stop_start()


