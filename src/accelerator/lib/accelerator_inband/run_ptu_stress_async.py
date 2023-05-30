import time
from lnx_exec_with_check import lnx_exec_command, lnx_exec_command_async
from constant import *


def copy_ptu():
    lnx_exec_command(f'mkdir -p {PTU_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=PTU_PATH_L)
    lnx_exec_command(f'cp -r {PTU_NAME} {PTU_PATH_L}')


def run_ptu_stress_async():
    """
          Purpose: Run ptu asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run ptu asynchronous stress overnight
                    run_ptu_stress_async()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    copy_ptu()
    lnx_exec_command('unzip *.zip', timeout=10*60, cwd=PTU_PATH_L)
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{PTU_PATH_L}')
    try:
        lnx_exec_command_async(f'./ptu -ct 8 > ptu_async-{current_time}.log', timeout=30, cwd=f'{PTU_PATH_L}')
    except Exception:
        pass


if __name__ == '__main__':
    run_ptu_stress_async()


