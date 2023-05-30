import set_toolkit_src_root
import time
import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from dtaf_core.lib.tklib.infra.sut import *

CASE_DESC = [
    'This testcase is to verify stress_FIO_Linux OS.',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>',
    'Storage_VMD_enable.py'
]


def get_raid_devices(sut):
    raid_devices_list = []
    get_devices_num = r'ls /dev/nvme*n1 | wc -l'
    devices_num = int(sut.execute_shell_cmd(get_devices_num)[1])

    for i in range(devices_num):
        cmd = f"cat /proc/partitions | grep nvme{i} | wc -l"
        ret = sut.execute_shell_cmd(cmd)[1]
        j = '/dev/nvme' + f'{i}' + 'n1'
        if int(ret) == 1:
            raid_devices_list.append(j)

    return raid_devices_list


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Check all the storage devices')
    log_dir_cmd = r'mkdir /root/log'
    sut.execute_shell_cmd(log_dir_cmd)
    log_dir = r'/root/log'
    show_devices_info = rf'fdisk -l > devices_info.txt'
    smartctl_cmd = rf'ls /dev/nvme*n1 | xargs -n 1 smartctl -a > smartctl.txt'
    sut.execute_shell_cmd(show_devices_info, cwd=log_dir)
    sut.execute_shell_cmd(smartctl_cmd, cwd=log_dir)

    Case.step('create data volume RAID5')
    raid_devices_list = get_raid_devices(sut)
    # format_raid_devices(sut, raid_devices_list)
    errmsg_list = []
    raid_cmd1 = rf'echo y | mdadm -C /dev/md/imsm0 {raid_devices_list[0]} {raid_devices_list[1]} {raid_devices_list[2]} -n 3 -e imsm'
    raid_cmd2 = rf'mdadm -C /dev/md/md0 /dev/md/imsm0 -n 3 -l 5'
    try:
        ret_code1 = sut.execute_shell_cmd(raid_cmd1, cwd=log_dir)[0]
        ret_code2, stdout2, stderr2 = sut.execute_shell_cmd(raid_cmd2, cwd=log_dir)
        errmsg_list.append(stderr2)
        Case.expect('create RAID 5 success', (ret_code1 or ret_code2) == 0)

        Case.step('check raid info')
        check_raid_cmd = r'mdadm -D /dev/md/md0 | tee RAID5.txt'
        stdout = sut.execute_shell_cmd(check_raid_cmd, cwd=log_dir)[1]
        Case.expect('check raid 5 info success', 'raid5' in stdout)
    except Exception as e:
        logger.info(e)
        logger.info(errmsg_list.pop())
        raise ValueError('create RAID 5 fail')
    finally:
        Case.step('remove RAID volume')
        stop_cmd = r'mdadm -S -s'
        check_md0_cmd = r'mdadm -D /dev/md/md0'
        expect_str = r'No such file or directory'
        zero_superblock_cmd = rf'mdadm --zero-superblock {raid_devices_list[0]} {raid_devices_list[1]} {raid_devices_list[2]}'
        ret_code4 = sut.execute_shell_cmd(stop_cmd, cwd=log_dir)[0]
        stderr2 = sut.execute_shell_cmd(check_md0_cmd, cwd=log_dir)[2]
        ret_code5 = sut.execute_shell_cmd(zero_superblock_cmd, cwd=log_dir)[0]
        Case.expect('stop RAID 5 success', ret_code4 == 0 and expect_str in stderr2)
        Case.expect('clean superblock success', ret_code5 == 0)

    Case.step('save log files')
    sut.download_to_local(remotepath=log_dir, localpath=os.path.join(LOG_PATH, 'result'))

    Case.step('restore env')
    del_log = r'rm -rf /root/log'
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

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
