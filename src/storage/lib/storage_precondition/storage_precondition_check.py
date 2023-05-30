#!/usr/bin/env python
# from src.lib.toolkit.auto_api import *
# from src.lib.toolkit.basic.utility import ParameterParser
# from src.lib.toolkit.infra.sut import get_default_sut
# from src.lib.toolkit.steps_lib.valtools.tools import *
# from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
# from src.configuration.config.sut_tool.sut_tools import SUT_TOOLS_LINUX_NETWORK
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.infra.sut import get_default_sut
from dtaf_core.lib.tklib.steps_lib.valtools.tools import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to


CASE_DESC = [
    "storage pre-condition check"
]


def test_steps(sut, sutos):
    assert (issubclass(sutos, GenericOS))
    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    if OS.get_os_family(sut.default_os) in SUT_STATUS.S0.LINUX_FAMILY:
        Case.step('Check fio install')
        sut.execute_cmd(sut, 'fio -v')

        Case.step('Check ilvss')
        sut.execute_cmd(sut, 'ls /opt/ilvss.0/ctc')

        Case.step('Check intelmas')
        sut.execute_cmd(sut, 'intelmas show -intelssd', timeout=60)

    if OS.get_os_family(sut.default_os) == SUT_STATUS.S0.WINDOWS:
        Case.step('Check iometer')
        ret, stdout, stderr = sut.execute_shell_cmd(f'Test-Path C:\BKCPkg\domains\storage\iometer\iometer.exe', powershell=True)
        stdout = stdout.split()
        if stdout[0] == 'False':
            exit(-1)

        Case.step('Check VROC CLI')
        ret, stdout, stderr = sut.execute_shell_cmd(f'Test-Path C:\BKCPkg\domains\storage\IntelVROCCli.exe', powershell=True)
        stdout = stdout.split()
        if stdout[0] == 'False':
            exit(-1)

        Case.step('Check VROC GUI')
        stdout = sut.execute_shell_cmd(r'wmic product get name, version')[1]
        logger.info(stdout)
        Case.expect('Install VROC driver successfully', 'Virtual RAID on CPU' in stdout)

        Case.step('Check Intelmas')
        Case.expect('Intel(R) Memory and Storage Tool install successfully ',
                    'Intel(R) Memory and Storage Tool' in stdout)


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
