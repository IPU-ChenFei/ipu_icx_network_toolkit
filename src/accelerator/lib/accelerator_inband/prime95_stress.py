import time
from lnx_exec_with_check import lnx_exec_command
from constant import *
from check_error import check_error


def copy_prime95_tool():
    lnx_exec_command(f'mkdir -p {PRIME95_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=PRIME95_PATH_L)
    lnx_exec_command(f'cp -r {PRIME95_NAME} {PRIME95_PATH_L}')


def copy_prime95_script():
    lnx_exec_command(f'cp -r {PRIME95_SCRIPT_NAME} {PRIME95_SCRIPT_PATH_L}')
    lnx_exec_command(f'cp -r {PPEXPECT_NAME} {PPEXPECT_prime95_PATH_L}')


def prime95_stress():
    """
          Purpose: Run prime95 stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run prime95 stress overnight
                  prime95_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    copy_prime95_tool()
    lnx_exec_command('tar -zxvf *.tar.gz', timeout=10 * 60, cwd=PRIME95_PATH_L)
    copy_prime95_script()
    ret, out, err = lnx_exec_command(f'python3 prime95.py run_prime95', timeout=3 * 60, cwd=PRIME95_PATH_L)
    check_error(err)
    lnx_exec_command(f'cp {PRIME95_PATH_L}primeprime-{current_time}.log {LOGS_L}')
    lnx_exec_command(f'cp {PRIME95_PATH_L}prime95-{current_time}.log {LOGS_L}')
    # self.sut.download_to_local(remotepath=f'{PRIME95_PATH_L}primeprime.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    # self.sut.download_to_local(remotepath=f'{PRIME95_PATH_L}prime95.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    _, out, err = lnx_exec_command(f'cat {PRIME95_PATH_L}primeprime*.log', timeout=60)
    check_error(err)
    _, out, err = lnx_exec_command(f'cat {PRIME95_PATH_L}prime95*.log', timeout=60)
    check_error(err)


if __name__ == '__main__':
    prime95_stress()



