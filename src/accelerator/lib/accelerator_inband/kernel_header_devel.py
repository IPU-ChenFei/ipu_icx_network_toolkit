from lnx_exec_with_check import lnx_exec_command
from constant import *


def kernel_header_devel():
    """
          Purpose: Install kernel-header and kernel-devel package
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install kernel-header and kernel-devel package
                  kernel_header_devel()
    """
    lnx_exec_command(f'mkdir -p {KERNEL_HEADER_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=KERNEL_HEADER_PATH_L)
    lnx_exec_command(f'cp -r {KERNEL_HEADER_NAME} {KERNEL_HEADER_PATH_L}')
    lnx_exec_command(f'cp -r {KERNEL_DEVEL_NAME} {KERNEL_HEADER_PATH_L}')
    lnx_exec_command('rpm -ivh *.rpm --force --nodeps', timeout=5*60, cwd=KERNEL_DEVEL_PATH_L)


if __name__ == '__main__':
    kernel_header_devel()



