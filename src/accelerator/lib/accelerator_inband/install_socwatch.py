from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *
from log import logger


def copy_socwatch():
    lnx_exec_command(f'mkdir -p {SOCWATCH_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=SOCWATCH_PATH_L)
    lnx_exec_command(f'cp -r {SOCWATCH_NAME} {SOCWATCH_PATH_L}')


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ll', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def install_socwatch():
    """
             Purpose: Install socwatch tool
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Install socwatch tool
                     install_socwatch()
       """
    copy_socwatch()
    lnx_exec_command('tar -zxvf *.tar.gz', timeout=60, cwd=SOCWATCH_PATH_L)
    folder_name = get_folder_name(SOCWATCH_PATH_L)
    _, out, err = lnx_exec_command('sh ./build_drivers.sh', timeout=60, cwd=f'{SOCWATCH_PATH_L}{folder_name}/')
    res, out, err = lnx_exec_command('insmod drivers/socwatch2_14.ko | wc -l', timeout=60, cwd=f'{SOCWATCH_PATH_L}{folder_name}/')
    if out != '0\n':
        logger.error('insmod socwatch.ko fail')
        raise Exception('insmod socwatch.ko fail')
    _, out, err = lnx_exec_command('source ./setup_socwatch_env.sh', timeout=60, cwd=f'{SOCWATCH_PATH_L}{folder_name}/')
    check_keyword(['SOCWATCH_BASE_DIR', 'SOCPERF_BASE_DIR'], out, 'config environment fail')


if __name__ == '__main__':
    install_socwatch()
