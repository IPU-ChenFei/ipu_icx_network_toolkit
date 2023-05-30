import set_toolkit_src_root
import datetime
import time
import os.path
from datetime import datetime

from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
# from src.configuration.config.wht.sut_tools import *
from src.storage.lib.storage import *

CASE_DESC = [
    'This testcase is to verify stress_Burnin_Win OS after enabling VMD.',
    # list the name of those cases which are expected to be executed before this case
    'Storage_VMD_enable.py'
]


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('clear EventLog')
    clear_syslog_cmd = r'clear-eventlog -log application, system'
    sut.execute_shell_cmd(clear_syslog_cmd, powershell=True)

    Case.step("create log folder")
    base_dir = rf'{SUT_TOOLS_WINDOWS_STORAGE}\BurnInTest'
    now_time = datetime.datetime.now().strftime('%Y%m%dZ%Hh%Mm%Ss')
    log_dir = rf'{base_dir}\log{now_time}'
    sut.execute_shell_cmd(rf'mkdir {log_dir}')

    Case.step("show disk and run BurnInTest")
    stress_time = ParameterParser.parse_parameter("stress_time")
    if stress_time == '':
        stress_time = 10
    else:
        stress_time = int(stress_time)
    sut.execute_shell_cmd("wmic diskdrive list brief > disk.txt",cwd=log_dir)
    sut.execute_shell_cmd_async(f"bit32.exe /c config.bitcfg /d {stress_time} /r", cwd=base_dir)
    # sut.execute_shell_cmd("bit32.exe /c config.bitcfg /d 1 /r",cwd="C:\Program Files\BurnInTest", timeout=80)
    time.sleep(stress_time * 60 + 300)
    sut.execute_shell_cmd("taskkill /f /t /im bit32.exe")

    try:
        Case.step('check EventLog')
        get_log_cmd = r'get-winevent system | where {($_.LevelDisplayName -match "Critical") -or ($_.LevelDisplayName -match "Error")}'
        check_log_cmd = rf"{get_log_cmd} | tee {log_dir}\event_log.txt"
        stdout = sut.execute_shell_cmd(check_log_cmd, powershell=True)[1]
        Case.expect('No Error or Critical log in EventLog', 'Error' not in stdout and 'Critical' not in stdout)

    finally:
        Case.step('save log files')
        sut.execute_shell_cmd(rf"xcopy {base_dir}\BIT_log.log {log_dir} ")
        sut.download_to_local(remotepath=log_dir, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        sut.execute_shell_cmd(rf"del {base_dir}\BIT_log.log")
        sut.execute_shell_cmd(rf"rd /s /q {log_dir}")

        Case.step('check stress result')
        stress_file_path = rf'{LOG_PATH}\result\log{now_time}\BIT_log.log'
        with open(stress_file_path, 'r', encoding='utf-16') as f:
            stress_result_text = f.read()
        Case.expect('run stress success', 'TEST RUN PASSED' in stress_result_text)


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
    # my_os = OperationSystem[sut.default_os]

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
