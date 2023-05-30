import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from qat_service_stop_start import qat_service_stop_start
from qat_service_restart import qat_service_restart
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Modify QAT config files'
                    '--config_key <modify config files> {asym, mdev, shim}')
    parser.add_argument('-c', '--config_key', required=True, dest='config_key', action='store', help='modify config files')
    ret = parser.parse_args(args)
    return ret


def __qat_mdev_config():
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    for i in range(cpu_num * QAT_DEVICE_NUM):
        lnx_exec_command(f'sed -i "s/NumberAdis = 0/NumberAdis = 16/g" /etc/4xxx_dev{i}.conf', timeout=60)
    qat_service_stop_start()


def __qat_shim_config():
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    for i in range(cpu_num * QAT_DEVICE_NUM):
        lnx_exec_command(f'sed -i "s/\[SSL\]/\[SHIM\]/g" /etc/4xxx_dev{i}.conf', timeout=60)
        lnx_exec_command(f'sed -i "s/NumberCyInstances = 3/NumberCyInstances = 1/g" /etc/4xxx_dev{i}.conf', timeout=60)
        lnx_exec_command(f'sed -i "s/NumberDcInstances = 2/NumberDcInstances = 1/g" /etc/4xxx_dev{i}.conf', timeout=60)
        lnx_exec_command(f'sed -i "s/NumProcesses = 1/NumProcesses = 16/g" /etc/4xxx_dev{i}.conf', timeout=60)
        lnx_exec_command(f'sed -i "s/LimitDevAccess = 0/LimitDevAccess = 1/g" /etc/4xxx_dev{i}.conf', timeout=60)
    qat_service_restart()


def qat_asym_config():
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    for i in range(cpu_num*QAT_DEVICE_NUM):
        lnx_exec_command(f'sed -i "s/ServicesEnabled.*/ServicesEnabled = asym;dc/g" /etc/4xxx_dev{i}.conf', timeout=60)
    qat_service_restart()


def modify_qat_config_file(config_key):
    """
          Purpose: Modify QAT config files
          Args:
              config_key : Which function (asym, mdev, shim) config files need to modify
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Modify QAT asymmetric encrypted config files
                    modify_qat_config_file('asym')
    """
    if config_key == 'mdev':
        __qat_mdev_config()
    elif config_key == 'asym':
        qat_asym_config()
    elif config_key == 'shim':
        __qat_shim_config()
    else:
        logger.error('Input correct config keyword')
        raise Exception('Input correct config keyword')


if __name__ == '__main__':
    args_parse = setup_argparse()
    modify_qat_config_file(args_parse.config_key)



