import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.aurora.lib.aurora import DMIDECODE_PATH, SOCKET_NUM, MEMORY_NUM_PER_SOCKET
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014075385'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)

    Case.step('check memory size in OS')
    _, mem_info, _ = sut.execute_shell_cmd("./dmidecode -t 17 | grep -E 'Memory Device|Locator|Bank Locator'",
                                           cwd=DMIDECODE_PATH)

    Case.step('check Locator info for each socket')
    for socket_index in range(SOCKET_NUM):
        ret = re.findall(r'Locator: ' + f'CPU{socket_index}' + r'_DIMM_[A-Z]\d', mem_info)
        Case.expect(f'mem number is right for socket {socket_index}', len(ret) == MEMORY_NUM_PER_SOCKET)


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
