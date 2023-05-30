import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run DSA workqueues two groups two queues and user 1 test'
                    '--dsa_device_index <dsa device index> {Setup_Randomize_DSA_Conf.sh -c -F 1}')
    parser.add_argument('-c', '--dsa_device_index', required=True, dest='dsa_device_index', action='store', help='device index')
    ret = parser.parse_args(args)
    return ret


def dsa_wq_2g2q_user_1(dsa_device_index):
    """
          Purpose: Run DSA workqueues two groups two queues and user 1 test
          Args:
              dsa_device_index: DSA device index, index begin from 0
          Returns:
              None
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run DSA workqueues two groups two queues and user 1 test
                  dsa_wq_2g2q_user_1('0')
    """
    res, out, err = lnx_exec_command('accel-config load-config -c ./2g2q_user_1.conf | wc -l', timeout=60,
                                               cwd=f'{DSA_PATH_L}idxd-config-accel-config/test/configs/')
    if out != '0\n':
        logger.error('accel-config load-config fail')
        raise Exception('accel-config load-config fail')
    _, out, err = lnx_exec_command('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/test/configs/')
    check_keyword(['"grouped_workqueues"', '"grouped_engines"'], out, 'Not recognized grouped_workqueues')
    _, out, err = lnx_exec_command(f'accel-config enable-device dsa{dsa_device_index}', timeout=60,
                                   cwd=f'{DSA_PATH_L}idxd-config-accel-config/test/configs/')
    check_keyword(['enabled 1 device(s) out of 1'], err, 'Enable dsa device fail')
    _, out, err = lnx_exec_command(
        f'accel-config enable-wq dsa{dsa_device_index}/wq0.0 dsa{dsa_device_index}/wq0.1', timeout=60,
        cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    check_keyword(['enabled 2 wq(s) out of 2'], err, 'Not all workqueues are enabled')
    _, out, err = lnx_exec_command('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    check_keyword(['"state":"enabled"'], out, 'Not recognized grouped_workqueues')
    _, out, err = lnx_exec_command(
        f'accel-config disable-wq dsa{dsa_device_index}/wq0.1 dsa{dsa_device_index}/wq0.0', timeout=60,
        cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    check_keyword(['disabled 2 wq(s) out of 2'], err, 'Not all workqueues are disabled')
    _, out, err = lnx_exec_command(f'accel-config disable-device dsa{dsa_device_index}', timeout=60,
                                   cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    check_keyword(['disabled 1 device(s) out of 1'], err, 'Disable dsa device fail')
    _, out, err = lnx_exec_command('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/test/configs/')
    if 'grouped_workqueues' in out or '"grouped_engines"' in out:
        logger.error('disable workqueues fail')
        raise Exception('disable workqueues fail')


if __name__ == '__main__':
    args_parse = setup_argparse()
    dsa_wq_2g2q_user_1(args_parse.dsa_device_index)


