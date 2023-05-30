# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib import cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.lib.toolkit.steps_lib.uefi_scene import BIOS_Menu

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016909529'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Bios')
    boot_to(sut, SUT_STATUS.S0.BIOS_MENU)

    Case.step('do a reset from bios')
    BIOS_Menu.reset_to_os(sut)


def clean_up(sut):
    cleanup.default_cleanup(sut)


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
