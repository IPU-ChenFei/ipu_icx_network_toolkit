import set_toolkit_src_root
import time
import os
from datetime import datetime

from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'Verify the performance of storage devices  using ILVSS tool on RHEL OS',
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
    Case.prepare('case prepare description')
    boot_to(sut, sut.default_os)

    Case.step('clear system log')
    now_time = datetime.datetime.now().strftime('%Y%m%dZ%Hh%Mm%Ss')
    clear_dmesg_cmd = r'dmesg -C'
    sut.execute_shell_cmd(clear_dmesg_cmd)
    clear_message_log = rf'cp /var/log/messages /var/log/messages_{now_time} && echo "" > /var/log/messages'
    sut.execute_shell_cmd(clear_message_log)

    Case.step('create log folder')
    base_dir = rf'/opt/ilvss.0'
    log_dir = rf'{base_dir}/log{now_time}'
    sut.execute_shell_cmd(rf'mkdir {log_dir}')

    Case.step("create raid 0 and mount")
    raid_devices_list = get_raid_devices(sut)
    errmsg_list = []
    create_monut_folder = 'mkdir /mnt/raid0'
    raid_create = rf'mdadm --create /dev/md0 --chunk=64 --level=0 --raid-devices=2 {raid_devices_list[0]} {raid_devices_list[1]}'
    raid_format = 'mkfs.ext4 -F /dev/md0'
    raid_monut = 'mount -t ext4 /dev/md0 /mnt/raid0'
    raid_info = rf'df -h > {log_dir}'
    try:
        sut.execute_shell_cmd(create_monut_folder, cwd=log_dir)
        ret_code1 = sut.execute_shell_cmd(raid_create, cwd=log_dir)[0]
        Case.expect('create RAID 0 success', ret_code1 == 0)
        sut.execute_shell_cmd(raid_format, cwd=log_dir)
        sut.execute_shell_cmd(raid_monut, cwd=log_dir)
        sut.execute_shell_cmd(raid_info, cwd=log_dir)

        Case.step('check raid info')
        check_raid_cmd = r'mdadm -D /dev/md0 | tee RAID0.txt'
        stdout = sut.execute_shell_cmd(check_raid_cmd, cwd=log_dir)[1]
        Case.expect('check raid 0 info success', 'raid0' in stdout)
    except Exception as e:
        logger.info(e)
        logger.info(errmsg_list.pop())
        raise ValueError('create RAID 0 fail')

    Case.step('run stress')
    stress_time = ParameterParser.parse_parameter("stress_time")
    if stress_time == '':
        stress_time = 10
    else:
        stress_time = int(stress_time)
    if sut.socket_name == 'SPR':
        iwvss_stress_cmd = rf'/opt/ilvss.0/ctc /PKG stress_platform.pkx /reconfig /CFG Platform /FLOW S145 /RUN /FD /MINUTES {stress_time} /PASSFILE {log_dir}/pass.txt /QUITPASS /RR {log_dir}/ilVSS.txt'
    else:
        iwvss_stress_cmd = rf'/opt/ilvss.0/ctc /PKG ICX_storage.pkx /reconfig /CFG Whitley /FLOW S145 /RUN /FD /MINUTES {stress_time} /PASSFILE {log_dir}/pass.txt /QUITPASS /RR {log_dir}/ilVSS.txt'
    sut.execute_shell_cmd_async(iwvss_stress_cmd, cwd=base_dir)
    time.sleep(stress_time * 60 + 300)

    try:
        Case.step('check system log')
        check_dmesg_cmd = rf"dmesg | tee {log_dir}/dmesg_log.txt"
        check_message_cmd = rf"cat /var/log/messages | tee {log_dir}/message_log.txt"
        stdout1 = sut.execute_shell_cmd(check_dmesg_cmd, cwd=log_dir)[1]
        stdout2 = sut.execute_shell_cmd(check_message_cmd, cwd=log_dir)[1]
        stdout = stdout1 + '\n' + stdout2
        key_word = ['Hardware Error']
        Case.expect('No Error or Fail log in system log', not any(i in stdout for i in key_word))

    finally:
        Case.step('save log files')
        sut.download_to_local(remotepath=log_dir, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('umount raid0')
        umount_cmd = r'umount /mnt/raid0'
        sut.execute_shell_cmd(umount_cmd, cwd=log_dir)

        Case.step('remove RAID volume')
        stop_cmd = r'mdadm -S -s'
        check_md0_cmd = r'mdadm -D /dev/md0'
        expect_str = r'No such file or directory'
        zero_superblock_cmd = rf'mdadm --zero-superblock {raid_devices_list[0]} {raid_devices_list[1]}'
        ret_code2 = sut.execute_shell_cmd(stop_cmd, cwd=log_dir)[0]
        stderr = sut.execute_shell_cmd(check_md0_cmd, cwd=log_dir)[2]
        ret_code3 = sut.execute_shell_cmd(zero_superblock_cmd, cwd=log_dir)[0]
        Case.expect('remove RAID 0 success', ret_code2 == 0 and expect_str in stderr)
        Case.expect('clean superblock success', ret_code3 == 0)

        Case.step('remove log folder')
        sut.execute_shell_cmd(f'rm -rf {log_dir}')
        sut.execute_shell_cmd(f'rm -rf /mnt/raid0')

        Case.step('check stress result')
        pass_file_path = rf'{LOG_PATH}\result\log{now_time}\pass.txt'
        Case.expect('run stress success', os.path.isfile(pass_file_path))


def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # sut.set_bios_knobs(*bios_knob('disable_wol_s5_xmlcli'))

    # TODO: replace default cleanup.to_S5 if necessary when case execution fail
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
