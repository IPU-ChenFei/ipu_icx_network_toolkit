from src.storage.lib.modify_iometer_cfg import *
from src.storage.lib.storage import *

CASE_DESC = [
    'This testcase is to verify stress_IOMeter_Win OS.',
    # list the name of those cases which are expected to be executed before this case
]


def is_iometer_running(sut):
    _, stdout, _ = sut.execute_shell_cmd('tasklist /FI \"IMAGENAME eq IOmeter.exe\"')
    if 'IOmeter.exe' in stdout:
        return True
    else:
        return False


def is_iometer_not_running(sut):
    return not is_iometer_running(sut)


def test_steps(sut, my_os):
    Case.prepare('case prepare description')
    boot_to(sut, sut.default_os)

    Case.step('clear EventLog')
    clear_syslog_cmd = r'clear-eventlog -log application, system'
    sut.execute_shell_cmd(clear_syslog_cmd, powershell=True)

    Case.step('create log folder')
    base_dir = rf'{SUT_TOOLS_WINDOWS_STORAGE}\iometer'
    now_time = datetime.datetime.now().strftime('%Y%m%dZ%Hh%Mm%Ss')
    log_dir = rf'{base_dir}\log{now_time}'
    sut.execute_shell_cmd(rf'mkdir {log_dir}')

    Case.step('get iometer configuration')
    dev_data = get_device_info(sut)
    cfg_file = rf'C:\BKCPkg\iometer.icf'
    stress_time = ParameterParser.parse_parameter("stress_time")
    if stress_time == '':
        stress_time = '0,10'
    else:
        stress_time = stress_time
    modify_cfg_file(dev_data, cfg_file, stress_time)
    sut.upload_to_remote(localpath=cfg_file, remotepath=rf'{SUT_TOOLS_WINDOWS_STORAGE}\iometer')

    Case.step('show devices info')
    device_info_cmd = rf'wmic diskdrive list brief > {log_dir}\device_info.txt'
    sut.execute_shell_cmd(device_info_cmd, cwd=base_dir)

    Case.step('run iometer stress')
    # be ensure the stress_time is matched with the time value in iometer.icf
    iometer_stress_cmd = rf'IOmeter.exe /c iometer.icf /r {log_dir}\result.txt'
    sut.execute_shell_cmd_async(iometer_stress_cmd, cwd=base_dir)
    Case.wait_and_expect('iometer stress is running', 60 * 3, is_iometer_running, sut)
    time_data = stress_time.split(',')
    time_data = [int(i) for i in time_data]
    runtime = time_data[0]*60 + time_data[1]
    Case.wait_and_expect('wait for iometer stress finish', runtime * 60 + 120, is_iometer_not_running, sut,
                         interval=60)

    try:
        Case.step('check EventLog')
        get_log_cmd = r'get-winevent system | where {($_.LevelDisplayName -match "Critical") -or ($_.LevelDisplayName -match "Error")}'
        check_log_cmd = rf"{get_log_cmd} | tee {log_dir}\event_log.txt"
        stdout = sut.execute_shell_cmd(check_log_cmd, powershell=True)[1]
        Case.expect('No Error or Critical log in EventLog', 'Error' not in stdout and 'Critical' not in stdout)

    finally:
        Case.step('save log files')
        sut.download_to_local(remotepath=log_dir, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        sut.execute_shell_cmd(f'rd /s /q {log_dir}')

        Case.step('check stress result')
        stress_file_path = rf'{LOG_PATH}\result\log{now_time}\result.txt'
        with open(stress_file_path, 'r') as f:
            stress_result_text = f.read()
        Case.expect('run stress success', 'End Test' in stress_result_text)


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
