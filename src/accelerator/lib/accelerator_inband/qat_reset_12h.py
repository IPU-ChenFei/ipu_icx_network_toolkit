import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger
import time
from run_qat_sample_code import run_qat_sample_code

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='mode of resetting'
                    '--mode <mode of resetting>')
    parser.add_argument('-m', '--mode', required=True, dest='mode', action='store',
                        help='mode of resetting, "all" or "adf"')
    ret = parser.parse_args(args)
    return ret

def qat_reset_12h(mode):
    """
          Purpose: run the qat reset for 12 hours
          Args:
              mode: mode of resetting
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: run the qat reset for 12 hours in 'for' mode
                  qat_reset_12h('virtual')
    """
    time_start = time.time()
    time_end = time.time()
    while (int(time_end) - int(time_start)) < 12*60*60:
        if str(mode) == 'virtual':
            lnx_exec_command('for i in {8..135}; do ./adf_ctl qat_dev$i restart ; done', timeout=60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
            run_qat_sample_code('signOfLife=1')
        elif str(mode) == 'physical':
            lnx_exec_command('adf_ctl restart', timeout=60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
            run_qat_sample_code()
        else:
            logger.error('Mode error, the running mode should either be physical or virtual')
            raise Exception('The running mode should either be physical or virtual')
        time_end = time.time()
    return


if __name__ == '__main__':
    args_parse = setup_argparse()
    qat_reset_12h(args_parse.mode)



