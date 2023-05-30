# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step, restore_bios_defaults_xmlcli_step
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import BURNIN_TEST_PATH, PMUTIL_BIN_PATH, PTU_PATH
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014074574',
]

TEST_DURATION = 5  # unit is minute


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)
    set_bios_knobs_step(sut, *bios_knob('disable_ISS_xmlcli'), *bios_knob('disable_PM_Turbo_mode_xmlcli'))
    Case.sleep(120)

    Case.step('get socket TDP')
    ret, stdout, _ = sut.execute_shell_cmd("./pmutil_bin -i | grep TDP | grep Socket | awk -F ':' '{print $2}'",
                                           cwd=PMUTIL_BIN_PATH)
    stdout = stdout.strip().split('\n')
    socket_tdp = [int(item.strip()[:-1]) for item in stdout]

    Case.step('Run BurnIn Test')
    # BurnInTest Linux cmdline parameters
    #   -B: BurnInTest will run in a silent mode and not create a ncurses/terminal window.
    #   -D: Sets the test duration to the value specified  in minutes
    sut.execute_shell_cmd_async(f'./bit_cmd_line_x64 -B -D {TEST_DURATION}', cwd=BURNIN_TEST_PATH)

    Case.step('Run Ptu monitor')
    sut.execute_shell_cmd(f'./ptu -mon -t {TEST_DURATION * 60} > default_TDP.log',
                          timeout=TEST_DURATION * 60 * 1.5, cwd=PTU_PATH)

    Case.step('check actual TDP')
    # 1st column is time, 2nd column is cpu name, 19th column is TDP
    ret, stdout, _ = sut.execute_shell_cmd(r"cat default_TDP.log | grep CPU[0-9] | awk '{print $1,$2,$19}'",
                                           timeout=TEST_DURATION * 60 * 1.5, cwd=PTU_PATH)
    for tdp in stdout.strip().split('\n'):
        tdp = tdp.strip().split()
        logger.debug(f'{tdp[1]} TDP is {tdp[2]}W at {tdp[0]} second')
        socket_index = int(tdp[1][3:])
        Case.expect('real TDP is lower than TDP setting', float(tdp[2]) < socket_tdp[socket_index])


def clean_up(sut):
    restore_bios_defaults_xmlcli_step(sut, sut.SUT_PLATFORM)

    default_cleanup(sut)


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <sut ini file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(default_sut=sut, desc_lines=CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
