from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *
from log import logger
from check_error import check_error


def copy_dsa():
    lnx_exec_command(f'mkdir -p {DSA_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=f'{DSA_PATH_L}')
    lnx_exec_command(f'unzip -o {DSA_NAME} -d {DSA_PATH_L}')


def accel_config_install():
    """
          Purpose: Install DSA SIOV accel_config
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install DSA SIOV accel_config
                  accel_config_install()
    """
    copy_dsa()
    #_, out, err = lnx_exec_command('ls', timeout=60, cwd='/sys/bus/dsa/')
    #check_keyword(['devices', 'drivers', 'drivers_autoprobe', 'drivers_probe', 'uevent'], out, 'all driver exist')
    #_, out, err = lnx_exec_command('ls |grep dsa', timeout=60, cwd='/sys/bus/dsa/devices/')
    #check_keyword(['dsa'], out, 'Not recognize all dsa device')
    lnx_exec_command('mv idxd-config* idxd-config-accel-config', timeout=20, cwd=f'{DSA_PATH_L}')
    _, out, err = lnx_exec_command('./autogen.sh', timeout=20 * 60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    lnx_exec_command(
        "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 --enable-test=yes", timeout=60,
        cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    _, out, err = lnx_exec_command('make', timeout=20 * 60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    check_error(err)
    #_, out, err = lnx_exec_command('make check', timeout=40 * 60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    #check_error(err)
    _, out, err = lnx_exec_command('make install', timeout=20 * 60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    check_error(err)
    _, out, err = lnx_exec_command('accel-config --list-cmds', timeout=5 * 60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    #check_keyword(
    #    ['version', 'list', 'load-config', 'save-config', 'help', 'disable-device', 'enable-device', 'disable-wq',
    #     'enable-wq', 'config-device', 'config-group', 'config-wq', 'config-engine', 'create-mdev', 'remove-mdev'], out, 'accel-config show fail')
    _, out, err = lnx_exec_command('accel-config list -i', timeout=5 * 60, cwd=f'{DSA_PATH_L}idxd-config-accel-config/')
    #check_keyword(['dsa'], out, 'No DSA device are detected')


if __name__ == '__main__':
    accel_config_install()
