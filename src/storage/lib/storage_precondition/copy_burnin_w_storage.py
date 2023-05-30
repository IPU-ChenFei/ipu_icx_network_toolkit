#!/usr/bin/env python

from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.infra.sut import get_default_sut
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.valtools.tools import *

CASE_DESC = [
    "Copy Burnin to windows sut"
]


def test_steps(sut, sutos):
    tools = get_tool(sut)

    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    Case.step('Download and uncompress')
    tools.get('burnin_w_storage').uncompress_to(method='zip')


def clean_up(sut):
    cleanup.default_cleanup(sut)
    # pass


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
