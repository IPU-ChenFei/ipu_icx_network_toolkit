import time
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger
from check_error import check_error


def copy_mlc():
    lnx_exec_command(f'mkdir -p {MLC_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=MLC_PATH_L)
    lnx_exec_command(f'cp -r {MLC_NAME} {MLC_PATH_L}')


def mlc_stress():
    """
          Purpose: Run mlc stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run mlc stress overnight
                    mlc_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    copy_mlc()
    lnx_exec_command('tar -zxvf *.tgz', timeout=10 * 60, cwd=MLC_PATH_L)
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{MLC_PATH_L}Linux/')
    _, out, err = lnx_exec_command(f'./mlc --loaded_latency -t5 -X -D8192 > mlc-{current_time}.log', timeout=50000,
                                   cwd=f'{MLC_PATH_L}Linux/')
    lnx_exec_command(f'cp {MLC_PATH_L}Linux/mlc*.log {LOGS_L}')
    check_error(err)


if __name__ == '__main__':
    mlc_stress()



