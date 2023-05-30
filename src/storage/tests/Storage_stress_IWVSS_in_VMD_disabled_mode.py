import set_toolkit_src_root
import time
import os
from datetime import datetime

from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
# from src.configuration.config.wht.sut_tools import *
from src.storage.lib.storage import *

CASE_DESC = [
    'To start the iwvss stress tool on the pcie nvme drives.',
    # list the name of those cases which are expected to be executed before this case
]


def test_steps(sut, my_os):
    Case.prepare('case prepare description')
    boot_to(sut, sut.default_os)

    Case.step('clear EventLog')
    clear_syslog_cmd = r'clear-eventlog -log application, system'
    sut.execute_shell_cmd(clear_syslog_cmd, powershell=True)

    Case.step('create log folder')
    base_dir = rf'{SUT_TOOLS_WINDOWS_STORAGE}\iwVSS'
    now_time = datetime.datetime.now().strftime('%Y%m%dZ%Hh%Mm%Ss')
    log_dir = rf'{base_dir}\log{now_time}'
    sut.execute_shell_cmd(rf'mkdir {log_dir}')

    Case.step('run iwvss stress')
    stress_time = ParameterParser.parse_parameter("stress_time")
    if stress_time == '':
        stress_time = 10
    else:
        stress_time = int(stress_time)
    if sut.socket_name == 'SPR':
        iwvss_stress_cmd = rf'ctc.exe /PKG EGS_NoBMC.pkx /reconfig /CFG EGS /FLOW S145 /RUN /FD /MINUTES {stress_time} /PASSFILE {log_dir}\pass.txt /QUITPASS /RR {log_dir}\iwVSS.txt'
    else:
        iwvss_stress_cmd = rf'ctc.exe /PKG ICX_storage.pkx /reconfig /CFG Whitley /FLOW S145 /RUN /FD /MINUTES {stress_time} /PASSFILE {log_dir}\pass.txt /QUITPASS /RR {log_dir}\iwVSS.txt'
    sut.execute_shell_cmd_async(iwvss_stress_cmd, cwd=base_dir)
    time.sleep(stress_time * 60 + 1800)

    try:
        Case.step('check EventLog')
        # check_log_cmd = rf'Get-EventLog -LogName System | tee {log_dir}\event_log.txt'
        get_log_cmd = r'get-winevent system | where {($_.LevelDisplayName -match "Critical") -or ($_.LevelDisplayName -match "Error")}'
        check_log_cmd = rf"{get_log_cmd} | tee {log_dir}\event_log.txt"
        stdout = sut.execute_shell_cmd(check_log_cmd, powershell=True)[1]
        Case.expect('No Error or Critical log in EventLog', 'Hardware Error' not in stdout)

    finally:
        Case.step('save log files')
        sut.download_to_local(remotepath=log_dir, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        sut.execute_shell_cmd(f'rd /s /q {log_dir}')

        Case.step('check stress result')
        pass_file_path = rf'{LOG_PATH}\result\log{now_time}\pass.txt'
        Case.expect('run iwvss stress success', os.path.isfile(pass_file_path))


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
