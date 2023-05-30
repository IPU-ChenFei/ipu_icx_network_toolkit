import datetime

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
def format_ssd(sut):
    device_name = sut.execute_shell_cmd("wmic diskdrive get /value | find \"Name=\\\"")[1].strip().split('\n\n')
    device_name1 = [i.split('\\')[3] for i in device_name]
    partitions_num = sut.execute_shell_cmd(r'wmic diskdrive get /value | find "Pa"')[1].strip().split('\n\n')
    dict1 = dict(zip(device_name1,partitions_num))
    ssd_list = []
    for i in device_name1:
        print(dict1.get(i))
        if dict1.get(i) == "Partitions=0":
            ssd_list.append(i)
    return ssd_list

def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Create log folder')
    nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = f'mkdir C:\\log_{nowTime}'
    sut.execute_shell_cmd(log_dir)
    remote_path = f'C:\\log_{nowTime}'

    Case.step('update storage SSD FW')
    # sut.execute_shell_cmd(rf'intelMAS.exe show -intelssd > intelssd.txt',cwd=remote_path)
    sut.execute_shell_cmd(rf'intelMAS.exe show -intelssd > {remote_path}\intelssd.txt',cwd="C:\Program Files\Intel\Intel(R) Memory and Storage Tool")
    format_ssd_list = format_ssd(sut)
    ssd_index = sut.execute_shell_cmd("intelMAS.exe show -intelssd |find \"Index\"",cwd="C:\Program Files\Intel\Intel(R) Memory and Storage Tool")[1].strip().split('\n')
    ssd_index1 = [i.split(' : ')[1] for i in ssd_index]
    DevicePath = sut.execute_shell_cmd("intelMAS.exe show -intelssd |find \"DevicePath\"",cwd="C:\Program Files\Intel\Intel(R) Memory and Storage Tool")[1].strip().split('\n')
    DevicePath1 = [i.split("\\.\\")[1]for i in DevicePath]
    all_device = dict(zip(DevicePath1, ssd_index1))
    get_updatssd = format_ssd_list

    for i in range(0, len(get_updatssd)):
        index = all_device.get(get_updatssd[i])
        print(index)
        sut.execute_shell_cmd(rf'echo y|IntelMAS.exe load -intelssd {index} >> {remote_path}\update.txt',cwd="C:\Program Files\Intel\Intel(R) Memory and Storage Tool")

    Case.step('save log files')
    sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

    Case.step('restore env')
    sut.execute_shell_cmd(f'rd /s /q {remote_path}')

    Case.step("check update log")
    check_log = os.path.join(LOG_PATH,'result',f'log_{nowTime}','update.txt')
    with open(check_log) as f:
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
