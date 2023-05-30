# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.lib.toolkit.steps_lib.uefi_scene import UefiShell, BIOS_Menu

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014074700'
]

TEST_CYCLE = 10


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Bios')
    boot_to(sut, SUT_STATUS.S0.BIOS_MENU)

    Case.step('set UEFI shell as the first boot order')
    sut.bios.set_default_boot_dev(sut.supported_os[SUT_STATUS.S0.UEFI_SHELL].dev)
    sut.bios.back_to_bios_setup(level=2)
    BIOS_Menu.enter_uefi_shell(sut)

    for i in range(TEST_CYCLE):
        Case.step(f'----start {i + 1} cycle----')
        sut.bios.uefi_shell.execute(UefiShell.wr_cmd)
        Case.sleep(30)
        Case.wait_and_expect('system will boot to uefi', 5 * 60, sut.bios.in_uefi)


def clean_up(sut):
    if Result.returncode != 0:
        sut.dc_off()
        Case.sleep(60)
        sut.dc_on()
        Case.sleep(30)
        sut.bios.enter_bios_setup()
    else:
        UefiShell.exit_to_bios_menu(sut)

    # restore default os boot to the first boot order
    sut.bios.set_default_boot_dev(sut.supported_os[sut.default_os_boot].dev)
    sut.bios.back_to_bios_setup(level=2)


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
