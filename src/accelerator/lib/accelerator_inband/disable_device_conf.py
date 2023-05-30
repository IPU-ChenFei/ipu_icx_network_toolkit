import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Disable accelerator device {Setup_Randomize_DSA_Conf.sh -d}'
                    '--acce_ip <accelerator type> {dsa, iax, qat, dlb}')
    parser.add_argument('-a', '--acce_ip', required=True, dest='acce_ip', action='store', help='accelerator type')
    ret = parser.parse_args(args)
    return ret


def disable_device_conf(disable_num, acce_ip):
    """
         Purpose: Disable work-queues
         Args:
             device_num: The number of enabled device in work-queues
             acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Disable work-queues
                 disable_device_conf(device_num, 'DSA')
   """
    _, out, err = lnx_exec_command(f'./Setup_Randomize_{acce_ip}_Conf.sh -d', timeout=5 * 60,
                                   cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}accel-random-config-and-test-main/')
    line_list = out.strip().split('\n')
    dsa_disable_num = 0
    for line in line_list:
        if 'disabled 1 device(s) out of 1' in line:
            dsa_disable_num += 1
    if dsa_disable_num != int(disable_num):
        logger.error('Not all dsa device are disabled')
        raise Exception('Not all dsa device are disabled')


if __name__ == '__main__':
    args_parse = setup_argparse()
    disable_num = int((lnx_exec_command('cat /home/logs/enabled_num.log')[1]).strip())
    disable_device_conf(disable_num, args_parse.acce_ip)


