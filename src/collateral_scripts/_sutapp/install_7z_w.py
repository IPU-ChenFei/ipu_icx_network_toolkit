#!/usr/bin/env python
import os

from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.valtools.tools import get_tool
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.configuration.config.sut_tool.wht_sut_tools import SUT_TOOLS_WINDOWS_NETWORK


CASE_DESC = [
    "Install 7z to windows sut"
]


def test_steps(sut, sutos):
    tools = get_tool(sut)

    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    Case.step('Downlad and uncompress iperf3')
    tools.get('7z_w').uncompress_to(method='copy')

    Case.step('Install 7z')
    # create symbolic link to target file/directory if some version number are included inside uncompressed path
    # sutos.execute_cmd(sut, rf'mklink /D {SUT_TOOLS_WINDOWS_NETWORK}\iperf3, {tools.a7z_w.ipath}\{os.path.basename(tools.a7z_w.ipath)}', timeout=30)

    #Case.step('Run iperf3 in test script')
    sutos.execute_cmd(sut, rf'{SUT_TOOLS_WINDOWS_NETWORK}\7z\7z.exe -v', timeout=30)


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

