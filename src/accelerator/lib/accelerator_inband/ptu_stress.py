import sys
import time
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger


def copy_ptu():
    lnx_exec_command(f'mkdir -p {PTU_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=PTU_PATH_L)
    lnx_exec_command(f'cp -r {PTU_NAME} {PTU_PATH_L}')


def ptu_stress():
    """
          Purpose: Run ptu stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run ptu stress overnight
                    ptu_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    copy_ptu()
    lnx_exec_command('unzip *.zip', timeout=10 * 60, cwd=PTU_PATH_L)
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{PTU_PATH_L}')
    try:
        lnx_exec_command(f'./ptu -ct 8 > ptu-{current_time}.log', timeout=20, cwd=f'{PTU_PATH_L}')
    except Exception:
        pass
    lnx_exec_command(f'cp {PTU_PATH_L}ptu*.log {LOGS_L}')
    _, out, err = lnx_exec_command('cat ptu*.log', timeout=60, cwd=f'{PTU_PATH_L}')
    if 'error' in out:
        logger.error('Run ptu stress fail')
        raise Exception('Run ptu stress fail')


if __name__ == '__main__':
    ptu_stress()


