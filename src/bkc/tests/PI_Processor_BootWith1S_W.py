import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import *
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.steps_lib.bios_knob import *

CASE_DESC = [
    'Before test, must prepare the golden file follow bkc_uniq pre-condition setup file in bkc_uniq lib folder',
    'This case is used to verify if the SUT could boot with 1S processor in Windows OS, '
    'and the CPU/NIC/NVME/MEM info reported by OS match the HW configuration.',
    'boot system into OS, check system message & dmesg then clear',
    'bios setting disable EIST then reset into os and check message & dmesg',
    'check CPU information',
    'Check NIC&NVMe information',
    'Check memory information',
]


def test_steps(sut, my_os):
    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)

    try:
        Case.step('Create log folder')
        nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        log_dir = f'mkdir C:\\log_{nowTime}'
        sut.execute_shell_cmd(log_dir)
        remote_path = f'C:\\log_{nowTime}'

        # Step 1
        Case.step('boot OS, get system event log')
        sut.execute_shell_cmd('Get-WinEvent -LogName system | select-object | tee 1stlog', cwd=remote_path,
                              powershell=True)
        Case.step('clear system event log')
        sut.execute_shell_cmd('Powershell -Command "clear-eventlog -log application, system"', powershell=True)

        # Step 2
        Case.step('disable EIST in bios and reset ')
        set_bios_knobs_step(sut, *bios_knob("disable_SpeedStep_xmlcli"))
        my_os.warm_reset_cycle_step(sut)
        check_bios_knobs_step(sut, *bios_knob("disable_SpeedStep_xmlcli"))

        # Step 3
        Case.step('boot OS, check system event log')
        sut.execute_shell_cmd(
            'Get-WinEvent -LogName system | select-object | tee 2ndlog', cwd=remote_path,
            powershell=True)

        # Step 4
        Case.step('get cpu info')
        ret1, stdout1, stderr1 = sut.execute_shell_cmd('wmic cpu | tee cpu.txt', cwd=remote_path, powershell=True)
        Case.expect('successful', 'failed' not in stdout1)

        Case.step('check cpu log')
        ret_code, stdout, stderr = sut.execute_shell_cmd('.\\cpu_check.ps1',
                                                         cwd=f"C:\BKCPkg\domains\\bkc_uniq\sut_scripts",
                                                         powershell=True)
        Case.expect('cpu info check pass', 'PASS' in stdout)

        # Step 5
        Case.step('get NIC info')
        ret1, stdout1, stderr1 = sut.execute_shell_cmd('wmic nic get /value |tee nic.txt', cwd=remote_path,
                                                       powershell=True)
        Case.expect('successful', 'failed' not in stdout1)

        Case.step('get NVME info')
        ret1, stdout1, stderr1 = sut.execute_shell_cmd('wmic diskdrive  get /value | tee diskdrive.txt',
                                                       cwd=remote_path,
                                                       powershell=True)
        Case.expect('successful', 'failed' not in stdout1)

        Case.step('check NIC&nvme log')
        ret_code, stdout, stderr = sut.execute_shell_cmd('.\\nic_nvme_check.ps1',
                                                         cwd=f"C:\BKCPkg\domains\\bkc_uniq\sut_scripts",
                                                         powershell=True)
        Case.expect('nic&nvme info check pass', 'PASS' in stdout)

        # Step 6
        Case.step('get MEM info')
        ret1, stdout1, stderr1 = sut.execute_shell_cmd('wmic memorychip get /value | tee mem.txt', cwd=remote_path,
                                                       powershell=True)
        Case.expect('successful', 'failed' not in stdout1)

        Case.step('check MEM log')
        ret_code, stdout, stderr = sut.execute_shell_cmd('.\\mem_check.ps1',
                                                         cwd=f"C:\BKCPkg\domains\\bkc_uniq\sut_scripts",
                                                         powershell=True)
        Case.expect('mem info check pass', 'PASS' in stdout)

    finally:
        Case.step('save log files')
        sut.execute_shell_cmd(f'mv *_get.txt {remote_path}', cwd=f"C:\BKCPkg\domains\\bkc_uniq\sut_scripts",
                              powershell=True)
        sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        sut.execute_shell_cmd(f'rd /s /q {remote_path}')


def clean_up(sut):
    # from src.lib.toolkit.steps_lib import cleanup
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
