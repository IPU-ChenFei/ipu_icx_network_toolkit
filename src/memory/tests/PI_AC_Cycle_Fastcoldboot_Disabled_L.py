import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from src.memory.lib.memory import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import *
from dtaf_core.lib.tklib.steps_lib.uefi_scene import *
from dtaf_core.lib.tklib.steps_lib.bios_knob import *

CASE_DESC = [
    'The objective of this test case is used to AC cycle boot flow when fast boot is disabled',
    # list the name of those cases which are expected to be executed before this case
]


def test_steps(sut, my_os):

    Case.prepare('case prepare description')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('Attempt_Fast_Boot_disable_xmlcli'), *bios_knob('Attempt_Fast_Boot_Cold_disable_xmlcli'))

    clear_system_log(sut)

    log_dir = create_log_dir(sut)

    check_dimm_info_cmd = 'dmidecode -t 17 | grep -E -v "No|Vo" | grep "Size" | wc -l'
    knob_str = 'subBootMode'
    expect_str = 'subBootMode = ColdBoot'
    cycles = ParameterParser.parse_parameter("cycles")
    if cycles == '':
        cycles = 6
    else:
        cycles = int(cycles)
    try:
        for i in range(1, cycles):
            my_os.g3_cycle_step(sut)
            Case.step(f'Check the DIMM information -{i}')
            dimm_info_check(sut, check_dimm_info_cmd, 'hw_dimm_number')
            knob_line_in_bios_log = get_knob_info_in_cycle(knob_str)
            Case.expect('knob in bios log is as expect', knob_line_in_bios_log == expect_str)

        check_system_log(sut, log_dir)

    finally:
        save_log_files(sut, log_dir)
        restore_env(sut, log_dir)
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
