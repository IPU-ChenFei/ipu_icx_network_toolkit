import sys
import time
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger
from check_error import check_error


def __copy_mega_to_config():
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    for i in range(cpu_num * QAT_DEVICE_NUM):
        lnx_exec_command(f'cp /home/BKCPkg/domains/accelerator/mega_conf/mega.conf /etc/4xxx_dev{i}.conf', timeout=60)


def copy_sample_code():
    lnx_exec_command(f'mkdir -p {SAMPLE_CODE_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=SAMPLE_CODE_PATH_L)
    lnx_exec_command(f'cp -r {SAMPLE_CODE_NAME} {SAMPLE_CODE_PATH_L}')


def copy_mega_conf():
    lnx_exec_command(f'mkdir -p {MEGA_CONF_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=MEGA_CONF_PATH_L)
    lnx_exec_command(f'cp -r {MEGA_CONF_NAME} {MEGA_CONF_PATH_L}')


def copy_mega_script():
    lnx_exec_command(f'cp -r {PPEXPECT_NAME} {PPEXPECT_MEGA_PATH_L}')
    lnx_exec_command(f'cp -r {MEGA_SCRIPT_NAME} {MEGA_SCRIPT_PATH_L}')


def qat_stv_mega_test():
    """
          Purpose: Run QAT mega test
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run QAT mega test
                  qat_stv_mega_test()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    copy_sample_code()
    lnx_exec_command('tar -zxvf *.tar.gz', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
    lnx_exec_command('./build.sh', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
    copy_mega_conf()
    __copy_mega_to_config()
    lnx_exec_command('./build/adf_ctl restart', timeout=60, cwd=QAT_DRIVER_PATH_L)
    copy_mega_script()
    ret, out, err = lnx_exec_command(f'python3 mega_script.py run_testcli', cwd=MEGA_SCRIPT_PATH_L)
    lnx_exec_command(f'mv {MEGA_SCRIPT_PATH_L}mega.log {MEGA_SCRIPT_PATH_L}mega-{current_time}.log')
    lnx_exec_command(f'cp {MEGA_SCRIPT_PATH_L}mega*.log {LOGS_L}')
    check_error(err)
    _, out, err = lnx_exec_command(f'cat {MEGA_SCRIPT_PATH_L}mega*.log', timeout=60)
    mega_list = out.strip().split('\n')
    tms_pass_num = 0
    for line in mega_list:
        if 'TMS PASSED' in line:
            tms_pass_num += 1
    if tms_pass_num != 7:
        logger.error(err)
        raise Exception(err)

        
if __name__ == '__main__':
    qat_stv_mega_test()


