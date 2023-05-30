# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.os_scene import check_system_power_status, not_in_os
from src.lib.toolkit.infra.xtp.itp import CscriptsSemiStructured
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016909536',
    'check functionality of dirty warm reset',
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('boot to OS & launch cscripts')
    boot_to(sut, sut.default_os)

    Case.step('inject IERR error to trigger the Dirty warm reset')
    cs = CscriptsSemiStructured(globals(), locals())
    out = cs.execute('ei.injectIERR()')
    Case.expect('inject IERR successfully', 'IERR is detected on the system' in out)

    Case.step('check system warm reboot')
    Case.wait_and_expect("system will warm reboot", 60, not_in_os, sut)
    Case.wait_and_expect('wait for system warm reboot to OS', 60 * 15, sut.check_system_in_os)


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
