from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from add_environment_to_file import add_environment_to_file
from constant import *
from log import logger
from check_error import check_error


def copy_dlb_driver():
    lnx_exec_command(f'mkdir -p {DLB_DRIVER_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=DLB_DRIVER_PATH_L)
    lnx_exec_command(f'cp -r {DLB_DRIVER_NAME} {DLB_DRIVER_PATH_L}')


def copy_dpdk():
    lnx_exec_command(f'mkdir -p {DPDK_DRIVER_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=DPDK_DRIVER_PATH_L)
    lnx_exec_command(f'\cp -r {DPDK_DRIVER_NAME} {DPDK_DRIVER_PATH_L}')


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ls -l', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def run_dpdk():
    """
          Purpose: Install and Run DPDK test
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install and Run DPDK test
                  run_dpdk()
    """
    #copy_dlb_driver()
    #lnx_exec_command('unzip *.zip', timeout=60, cwd=DLB_DRIVER_PATH_L)
    copy_dpdk()
    lnx_exec_command('tar xfJ *.tar.xz', timeout=30*60, cwd=DPDK_DRIVER_PATH_L)
    folder_name = get_folder_name(DPDK_DRIVER_PATH_L)
    lnx_exec_command('yum -y install patch', timeout=30 * 60)
    _, out, err = lnx_exec_command(f'patch -Np1 < {DLB_DRIVER_PATH_L}/dpdk/dpdk_dlb_v20.11.3_2830917_diff.patch', timeout=30*60,
                                   cwd=f'{DPDK_DRIVER_PATH_L}{folder_name}/')
    #check_keyword(['succeeded'], out, 'DPDK load patch fail')
    add_environment_to_file('DPDK_DIR', f'export DPDK_DIR={DPDK_DRIVER_PATH_L}{folder_name}/')
    add_environment_to_file('RTE_SDK', 'export RTE_SDK=$DPDK_DIR')
    add_environment_to_file('RTE_TARGET', 'export RTE_TARGET=installdir')
    lnx_exec_command('source $HOME/.bashrc', timeout=10 * 60)
    lnx_exec_command('yum install -y meson', timeout=30 * 60)
    lnx_exec_command('pip3 install ninja', timeout=30 * 60)
    _, out, err = lnx_exec_command('meson setup --prefix $RTE_SDK/$RTE_TARGET builddir', timeout=60 * 60,
                                   cwd=f'{DPDK_DRIVER_PATH_L}{folder_name}/')
    check_error(err)
    lnx_exec_command('ninja -C builddir', timeout=30 * 60, cwd=f'{DPDK_DRIVER_PATH_L}{folder_name}/')
    lnx_exec_command('mkdir -p /mnt/hugepages', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}{folder_name}/')
    lnx_exec_command('mount -t hugetlbfs nodev /mnt/hugepages', timeout=30*60, cwd=f'{DPDK_DRIVER_PATH_L}{folder_name}/')
    lnx_exec_command('echo 2048 > /proc/sys/vm/nr_hugepages', timeout=30*60, cwd=f'{DPDK_DRIVER_PATH_L}{folder_name}/')


if __name__ == '__main__':
    run_dpdk()



