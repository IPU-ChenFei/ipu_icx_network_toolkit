import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger
import os

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='modify the specific line of a file'
                    '--mode <the mode of vqat operation>')
    parser.add_argument('-m', '--mode', default='sym', dest='mode', action='store', help='the mode of vqat operation,sym,dc,asym')
    ret = parser.parse_args(args)
    return ret



def enable_allqat_siov(mode):
    """
          
		  Enable sIOV on all QAT devices
          Args:
              mode: the mode of vqat 
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: execute './build/vqat_ctl create 0000:6b:00.0 sym'
                  enable_allqat_siov('sym')
    """
    return_code, out, err = lnx_exec_command('lspci |grep 4940', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
    line_list = out.strip().split('\n')
    if return_code:
        sys.exit(return_code)
    else:
        for line in line_list:
            bdf = line.split(' ')[0]
            return_code, out, err = lnx_exec_command('./build/vqat_ctl create' + ' ' + str(bdf) + ' ' + mode, timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
            if return_code:
                sys.exit(return_code)
    return


if __name__ == '__main__':
    args_parse = setup_argparse()
    enable_allqat_siov(args_parse.mode)



