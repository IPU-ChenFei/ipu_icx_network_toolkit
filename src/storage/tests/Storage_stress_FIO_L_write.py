import set_toolkit_src_root
import time
import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from dtaf_core.lib.tklib.infra.sut import *

CASE_DESC = [
    'This testcase is to verify stress_FIO_Linux OS after enabling VMD.',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>',
]


# def fio_stress_devices(sut):
#     show_devices = r'ls /dev/nvme*n1'
#     devices_list = sut.execute_shell_cmd(show_devices)[1].strip().split()
#     get_linux_os = r"df -h | grep /boot$ | awk '{print $1}' | grep -o .*n1"
#     linux_os_device = sut.execute_shell_cmd(get_linux_os)[1].strip()
#     get_win_os = r"fdisk -l | grep Windows | awk '{print $1}' | grep -o .*n1"
#     win_os_device = sut.execute_shell_cmd(get_win_os)[1].strip()
#     remove_os_list = [linux_os_device, win_os_device]
#     for i in remove_os_list:
#         devices_list.remove(i)
#     return devices_list
def fio_stress_devices(sut):
    fio_devices_list = []
    get_devices_num = r'ls /dev/nvme*n1 | wc -l'
    devices_num = int(sut.execute_shell_cmd(get_devices_num)[1])
    for i in range(devices_num):
        cmd = f"cat /proc/partitions | grep nvme{i} | wc -l"
        ret = sut.execute_shell_cmd(cmd)[1]
        j = '/dev/nvme' + f'{i}' + 'n1'
        if int(ret) == 1:
            fio_devices_list.append(j)
    return fio_devices_list


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Create log folder')
    nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = rf'mkdir /root/log_{nowTime}'
    sut.execute_shell_cmd(log_dir)
    remote_path = rf'/root/log_{nowTime}'

    Case.step('Check all the storage devices')
    show_devices_info = rf'fdisk -l > devices_info.txt'
    smartctl_cmd = rf'ls /dev/nvme*n1 | xargs -n 1 smartctl -a > smartctl.txt'
    sut.execute_shell_cmd(show_devices_info, cwd=remote_path)
    sut.execute_shell_cmd(smartctl_cmd, cwd=remote_path)

    Case.step('run fio stress')
    devices_list = fio_stress_devices(sut)
    hd_num = len(devices_list)
    stress_time = ParameterParser.parse_parameter("stress_time")
    if stress_time == '':
        stress_time = 300
    else:
        stress_time = int(stress_time)
    for i in range(hd_num):
        fio_stress_cmd = rf"fio -filename={devices_list[i]} -direct=1 -iodepth=16 -thread  -rw=write -ioengine=libaio -bs=64k \
        -size=300G -numjobs=1 -runtime={stress_time} -time_based -group_reporting -name=seq_100write64k > {devices_list[i].split('/')[-1]}.txt"
        sut.execute_shell_cmd_async(fio_stress_cmd, cwd=remote_path)
    if sut.is_simics:
        time.sleep(stress_time * 10)
    else:
        time.sleep(stress_time + 120)

    Case.step('save log files')
    sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

    Case.step('restore env')
    del_log = rf'rm -rf {remote_path}'
    sut.execute_shell_cmd(del_log)


def clean_up(sut):
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)
    pass


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <json file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
