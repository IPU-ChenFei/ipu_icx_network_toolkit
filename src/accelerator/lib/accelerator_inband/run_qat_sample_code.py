import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run QAT cap_sample stress'
                    '--qat_cpa_param <Running mode>')
    parser.add_argument('-q', '--qat_cpa_param', default='', dest='qat_cpa_param', action='store',
                        help='Running mode')
    ret = parser.parse_args(args)
    return ret


def run_qat_sample_code(qat_cpa_param=''):
    """
          Purpose: Run QAT cap_sample stress
          Args:
              qat_cpa_param: Which cap_sample stress need to run
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: run cap_sample stress
                    run_qat_sample_code('')
                    run_qat_sample_code('signOfLife=1')
    """
    _, out, err = lnx_exec_command('./cpa_sample_code ' + qat_cpa_param, timeout=1000 * 60,
                                   cwd=f'{QAT_DRIVER_PATH_L}/build/')
    check_keyword(['Sample code completed successfully'], out, 'Issue - Run qat stress fail')


if __name__ == '__main__':
    args_parse = setup_argparse()
    run_qat_sample_code(args_parse.qat_cpa_param)



