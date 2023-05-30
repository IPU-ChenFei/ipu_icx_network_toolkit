from lnx_exec_with_check import lnx_exec_command, lnx_exec_command_async
from constant import *


def copy_prime95_tool():
    lnx_exec_command(f'mkdir -p {PRIME95_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=PRIME95_PATH_L)
    lnx_exec_command(f'cp -r {PRIME95_NAME} {PRIME95_PATH_L}')


def copy_prime95_script():
    lnx_exec_command(f'cp -r {PRIME95_SCRIPT_NAME} {PRIME95_SCRIPT_PATH_L}')
    lnx_exec_command(f'cp -r {PPEXPECT_NAME} {PPEXPECT_prime95_PATH_L}')


def run_prime95_stress_async():
    """

          Purpose: Run prime95 asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run prime95 asynchronous stress overnight
                  run_prime95_stress_async()
    """
    copy_prime95_tool()
    lnx_exec_command('tar -zxvf *.tar.gz', timeout=10 * 60, cwd=PRIME95_PATH_L)
    copy_prime95_script()
    lnx_exec_command_async(f'{PRIME95_PATH_L}python3 prime95.py run_prime95')


if __name__ == '__main__':
    run_prime95_stress_async()



