import set_toolkit_src_root
import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from dtaf_core.lib.tklib.infra.sut import *
# from src.configuration.config.wht.sut_tools import *
from src.storage.lib.storage import *

CASE_DESC = [
    'This testcase is to verify install VROC in Win OS.',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>',
    'Storage_VMD_enable.py'
]


def test_steps(sut, my_os):
    # Prepare step
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Install VROC')
    folder = ParameterParser.parse_parameter("folder")
    if folder == '':
        folder = 'vroc_7.6.0.1020_PC_GUI'
    tool_path = SUT_TOOLS_WINDOWS_STORAGE + f'\{folder}\Install'
    sut.execute_shell_cmd(r'SetupVROC.exe /q', timeout=8*60, cwd=tool_path)
    stdout = sut.execute_shell_cmd(r'wmic product get name, version')[1]
    logger.info(stdout)
    Case.expect('Install VROC driver successfully', 'Virtual RAID on CPU' in stdout)



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
