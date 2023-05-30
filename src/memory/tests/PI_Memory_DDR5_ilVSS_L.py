import set_toolkit_src_root
from src.memory.lib.memory import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import *
from dtaf_core.lib.tklib.steps_lib.uefi_scene import *
from dtaf_core.lib.tklib.steps_lib.bios_knob import *
import os


CASE_DESC = [
    'This case is used to change the capacity of the system memory in the Simics script, and check whether the change works. ',
    # list the name of those cases which are expected to be executed before this case
]


def test_steps(sut, my_os):
    Case.prepare('case prepare description')
    # boot_to(sut, sut.default_os)
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('enable_enforce_POR_xmlcli'))

    clear_system_log(sut)

    log_dir = create_log_dir(sut)

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
    sut.execute_shell_cmd_async(iwvss_stress_cmd, cwd=r'/opt/ilvss.0')
    time.sleep(stress_time * 60 + 300)

    save_log_files(sut, log_dir)
    restore_env(sut, log_dir)

    Case.step('check stress result')
    pass_file_path = rf'{LOG_PATH}\result\log{now_time}\pass.txt'
    Case.expect('run stress success', os.path.isfile(pass_file_path))

    check_system_log(sut, log_dir)
    restore_bios_defaults_xmlcli_step(sut, SUT_STATUS.S0.LINUX)


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
