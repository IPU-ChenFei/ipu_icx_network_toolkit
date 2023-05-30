import time
from lnx_exec_with_check import lnx_exec_command, lnx_exec_command_async
from constant import *
from log import logger
from check_error import check_error


def copy_mlc():
    lnx_exec_command(f'mkdir -p {MLC_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=MLC_PATH_L)
    lnx_exec_command(f'cp -r {MLC_NAME} {MLC_PATH_L}')


def run_mlc_stress_async():
    """
          Purpose: Run mlc asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run mlc asynchronous stress overnight
                    run_mlc_stress_async()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf mlc_async*.log', timeout=60, cwd='/root/')
    copy_mlc()
    lnx_exec_command('tar -zxvf *.tgz', timeout=10 * 60, cwd=MLC_PATH_L)
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{MLC_PATH_L}Linux/')
    # lnx_exec_command_async(f'./mlc --loaded_latency -t3 -X -D8192 > mlc_async-{current_time}.log', timeout=50000, cwd=f'{MLC_PATH_L}Linux/')
    lnx_exec_command_async(f'{MLC_PATH_L}Linux/mlc --loaded_latency -t3 -X -D8192 > /root/mlc_async-{current_time}.log')


if __name__ == '__main__':
    run_mlc_stress_async()



