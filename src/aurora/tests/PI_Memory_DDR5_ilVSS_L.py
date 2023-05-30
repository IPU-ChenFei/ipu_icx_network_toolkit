# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.aurora.lib.aurora import ILVSS_PATH
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014075131'
]

STRESS_DURATION = 120  # unit is minute
TEST_PKG_NAME = 'memstress.pkx'
TEST_PC_NAME = 'Aurora'
TEST_FLOW_NAME = 'S145'


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)

    Case.step('run ilVSS tool')
    # delete old log file
    sut.execute_shell_cmd("rm SUMMARY_T.TXT", cwd=ILVSS_PATH)
    ret, _, _ = sut.execute_shell_cmd(
        f"./t /pkg {TEST_PKG_NAME} /reconfig /pc {TEST_PC_NAME} /flow {TEST_FLOW_NAME} /run /MINUTES {STRESS_DURATION}",
        cwd=ILVSS_PATH, timeout=(STRESS_DURATION + 10) * 60)
    Case.expect('ilvss test passed', ret == 0)

    Case.step('check ilvss log')
    _, stdout, _ = sut.execute_shell_cmd("cat SUMMARY_T.TXT", cwd=ILVSS_PATH)
    summary_log_all = str(stdout).splitlines()
    for i in range(1, len(summary_log_all)):
        summary_info = summary_log_all[i].split()
        # column 0 is test module name, column 2 is fail count, column 3 is error count
        Case.expect(f'{summary_info[0]} test fail is zero', summary_info[2] == '0')
        Case.expect(f'{summary_info[0]} test error is zero', summary_info[3] == '0')


def clean_up(sut):
    default_cleanup(sut)


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
