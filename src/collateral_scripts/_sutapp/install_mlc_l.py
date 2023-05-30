from src.lib.toolkit.basic.const import OS
from src.lib.toolkit.basic.testcase import Case, Result
from src.lib.toolkit.basic.utility import ParameterParser
from src.lib.toolkit.infra.sut import get_default_sut
from src.lib.toolkit.steps_lib.os_scene import GenericOS, OperationSystem
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    "it is a python script generated from validation language"
]

from src.lib.toolkit.steps_lib.vl.vltcd import *

def test_steps(sut, sutos):
    assert (issubclass(sutos, GenericOS))

    tools = get_tool(sut)

    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    # uninstall
    sutos.remove_folder(sut, tools.mlc_l.ipath)
    sutos.execute_cmd(sut, sutos.mkdir_cmd % tools.mlc_l.ipath)

    # install
    Case.step('deploy and install')
    tools.get('mlc_l').uncompress_to(method='tgz')

    Case.step("Run MLC to check")
    sutos.execute_cmd(sut, f'{tools.mlc_l.ipath}/Linux/mlc --peak_injection_bandwidth -Z -t60', timeout=10*60)


def clean_up(sut):
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
