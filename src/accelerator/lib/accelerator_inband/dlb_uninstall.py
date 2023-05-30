import sys
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger


def dlb_uninstall():
    """
         Purpose: to uninstall dlb driver
         Args:
             No
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: uninstall dlb driver
                 dlb_uninstall()
    """
    lnx_exec_command('rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
    _, out, err = lnx_exec_command('lsmod | grep dlb2 | wc -l', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
    if out != '0\n':
        logger.error('DLB driver uninstall failed')
        raise Exception('DLB driver uninstall failed')


if __name__ == '__main__':
    dlb_uninstall()


