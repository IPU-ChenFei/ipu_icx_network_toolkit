import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import *
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.steps_lib.bios_knob import *

CASE_DESC = [
    'Before test, must prepare the golden file follow bkc_uniq pre-condition setup file in bkc_uniq lib folder',
    'This case is used to verify if the cpu info in Linux OS ',
    'and the CPU/NIC/NVME/MEM info reported by OS match the HW configuration.',
    'boot system into OS, check system message & dmesg then clear',
    'bios setting disable EIST then reset into os and check message & dmesg',
    'check CPU information',
    'Check NIC&NVMe information',
    'Check memory information',
]


def test_steps(sut, my_os):
    boot_to(sut, sut.default_os)

    try:
        Case.step('Create log folder')
        nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        log_dir = rf'mkdir /root/log_{nowTime}'
        sut.execute_shell_cmd(log_dir)
        remote_path = rf'/root/log_{nowTime}'

        # Step 1-1
        Case.step('get message & dmesg at first')
        get_dmesg_cmd = r'dmesg >dmesg1'
        sut.execute_shell_cmd(get_dmesg_cmd, cwd=remote_path)
        get_messages_log = r'cp /var/log/messages messages1'
        sut.execute_shell_cmd(get_messages_log, cwd=remote_path)

        # Step 1-2
        Case.step('clear message & dmesg')
        clear_log_cmd = r'dmesg -c && cat /dev/null > /var/log/messages'
        sut.execute_shell_cmd(clear_log_cmd)

        # Step 2
        Case.step('disable EIST in bios and reset ')
        set_bios_knobs_step(sut, *bios_knob("disable_SpeedStep_xmlcli"))
        my_os.warm_reset_cycle_step(sut)
        check_bios_knobs_step(sut, *bios_knob("disable_SpeedStep_xmlcli"))

        # Step 3
        Case.step('get message & dmesg again')
        get_dmesg_cmd = r'dmesg >dmesg2'
        sut.execute_shell_cmd(get_dmesg_cmd, cwd=remote_path)
        get_messages_log = r'cp /var/log/messages messages2'
        sut.execute_shell_cmd(get_messages_log, cwd=remote_path)

        # Step 4
        Case.step('get cpu information')
        get_cpuinfo_cmd = r'cat /proc/cpuinfo > cpuinfo.txt && lscpu > lscpu.txt'
        sut.execute_shell_cmd(get_cpuinfo_cmd, cwd=remote_path)

        Case.step('check cpu log')
        ret_code, stdout, stderr = sut.execute_shell_cmd('./cpu_check.sh', cwd="/root/sut_scripts/bkc_uniq")
        Case.expect('cpu info check pass', 'PASS' in stdout)

    finally:
        Case.step('save log files')
        sut.execute_shell_cmd(f'mv *_get.txt {remote_path}', cwd="/root/sut_scripts/bkc_uniq")
        sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        del_log = rf'rm -rf {remote_path}'
        sut.execute_shell_cmd(del_log)


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
