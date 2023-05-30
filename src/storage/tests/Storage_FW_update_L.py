import datetime
import time

from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

# TODO: import your domain knobs define or define it here
#   Finally optimize import (shortcut key is 'Ctrl + Alt + O') before submitting code

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'This testcase is to verify Reboot cycling_Win OS.',
    '<dependencies: if any>'
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

    Case.step('Create log folder')
    nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = rf'mkdir /root/log_{nowTime}'
    sut.execute_shell_cmd(log_dir)
    remote_path = rf'/root/log_{nowTime}'

    Case.step('update storage SSD FW')
    sut.execute_shell_cmd('intelmas show -intelssd > intelssd.txt', cwd=remote_path)
    ssd_index = sut.execute_shell_cmd("intelmas show -intelssd |grep -i 'index' | cut -b 9")[1].split('\n')
    DevicePath = sut.execute_shell_cmd("intelmas show -intelssd |grep -i '/dev/' | cut -b 14-25")[1].split('\n')
    all_device = dict(zip(DevicePath, ssd_index))
    get_update_ssd = get_raid_devices(sut)

    for i in range(0, len(get_update_ssd)):
        index = all_device.get(get_update_ssd[i])
        print(index)
        sut.execute_shell_cmd(rf'echo y|intelmas load -intelssd {index} >> updatessd.txt',cwd=remote_path)



    Case.step('save log files')
    sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

    Case.step('restore env')
    del_log = rf'rm -rf /root/log_{nowTime}'
    sut.execute_shell_cmd(del_log)

    Case.step('check log')
    check_log = os.path.join(LOG_PATH,'result',f'log_{nowTime}','updatessd.txt')
    with open(f'{check_log}','r') as f:
        check_file = f.read()
        if "fail" in check_file:
            raise Exception("ssd FW update fail")
        else:
            Case.expect("update successful or is already the latest version","updated successfully" or "contains current firmware" in check_file)
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
