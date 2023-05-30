from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger
from check_error import check_error


def copy_qat_engine():
    lnx_exec_command(f'mkdir -p {QAT_ENGINE_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_ENGINE_PATH_L)
    lnx_exec_command(f'cp -r {QAT_ENGINE_NAME} {QAT_ENGINE_PATH_L}')


def qat_engine_install():
    """
          Purpose: Install QAT Engine file
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install QAT Engine file
                    qat_engine_install()
    """
    copy_qat_engine()
    lnx_exec_command('unzip *.zip', timeout=60, cwd=QAT_ENGINE_PATH_L)
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    lnx_exec_command('dos2unix *', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    _, out, err = lnx_exec_command('./autogen.sh', timeout=20 * 60,
                                   cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    _, out, err = lnx_exec_command(f'./configure  --with-qat_hw_dir={QAT_DRIVER_PATH_L}', timeout=20*60,
                                   cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_error(err)
    lnx_exec_command(
        f'sed -i "s/cpa_dc.h/dc\/cpa_dc.h/g" {QAT_DRIVER_PATH_L}/quickassist/lookaside/access_layer/include/icp_sal_user.h',
        timeout=60)
    _, out, err = lnx_exec_command('make install', timeout=20 * 60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_error(err)


if __name__ == '__main__':
    qat_engine_install()



