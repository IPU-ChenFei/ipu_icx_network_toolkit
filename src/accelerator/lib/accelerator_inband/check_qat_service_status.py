import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Check all QAT device status in output file'
                    '--is_vf <check QAT status with host or not>')
    parser.add_argument('-i', '--is_vf',  default=None, dest='is_vf', action='store', help='QAT status with host or not')
    ret = parser.parse_args(args)
    return ret


def __qat_service_status():
    """
          Purpose: Run QAT service status
          Args:
              No
          Returns:
              QAT service status result
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: run qat_service status
                    qat_service_status()
    """
    _, out, err = lnx_exec_command('service qat_service status', timeout=10*60)
    if "Unit qat_service.service could not be found" in err:
        _, out, err = lnx_exec_command('qat_service status', timeout=10*60)
        return out
    return out


def check_qat_service_status(is_vf=False):
    """
          Purpose: Check all QAT device status in output file
          Args:
              vf: Check QAT vf status or pf status
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Check all QAT device status in output file
                    check_all_device_status(True)-->check qat vf status
                    check_all_device_status(False)-->check qat pf status
    """
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    out = __qat_service_status()
    str_list = out.strip().split('\n')
    status_num = 0
    if is_vf:
        for line in str_list:
            if 'state: up' in line:
                status_num += 1
        if status_num != cpu_num * QAT_DEVICE_NUM * 17:
            logger.error('Not all QAT device status up or Not Recognize all QAT device')
            raise Exception('Not all QAT device status up or Not Recognize all QAT device')
    else:
        for line in str_list:
            if 'state: up' in line:
                status_num += 1
        if status_num != cpu_num * QAT_DEVICE_NUM:
            logger.error('Not all QAT device status up or Not Recognize all QAT device')
            raise Exception('Not all QAT device status up or Not Recognize all QAT device')


if __name__ == '__main__':
    args_parse = setup_argparse()
    check_qat_service_status(args_parse.is_vf)



