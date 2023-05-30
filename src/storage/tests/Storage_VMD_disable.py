import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib import cleanup
from src.storage.lib.storage import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import *
from dtaf_core.lib.tklib.steps_lib.bios_knob import *

CASE_DESC = [
    'This testcase is to verify enabling VMD through BIOS knobs change.',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    if sut.is_simics:
        # work around for simics
        Case.prepare('boot to OS')
        boot_to(sut, sut.default_os)
    else:
        Case.prepare('boot to UEFI')
        boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)

    Case.step('set VMD disable')
    if sut.socket_name == 'GNR':
        vmd_knobs = set_vmd('bhs_bios.xml', status='Disable')
    elif sut.socket_name == 'SPR':
        vmd_knobs = set_vmd('egs_bios.xml', status='Disable', vmd_list=[4, 5], weight=8)
    else:
        vmd_knobs = set_vmd('wht_bios.xml', status='Disable')
    set_bios_knobs_step(sut, *vmd_knobs)
    Case.sleep(5)

    Case.step('reboot to UEFI shell and check vmd setting')
    UefiShell.reset_cycle_step(sut)
    ret = check_bios_knobs_step(sut, *vmd_knobs)
    Case.expect('check vmd disable successful', ret)


def clean_up(sut):
    if Result.returncode != 0:
        cleanup.to_s5(sut)


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
