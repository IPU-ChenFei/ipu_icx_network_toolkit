import time

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.os_scene import check_system_power_status
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014074438',
    'Verify the SUT can boot from S5 status'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)

    for i in range(10):
        logger.info(f'start No.{i} graceful shut down cycle')

        Case.step('clear dmesg before shutdown')
        ret, _, _ = sut.execute_shell_cmd('dmesg -C')
        Case.expect('clear dmesg successfully', ret == 0)

        Case.step('shutdown OS')
        sut.execute_shell_cmd('shutdown -h now')
        Case.sleep(30)
        Case.wait_and_expect("system power status = S5", 300, check_system_power_status, sut, SUT_STATUS.S5)

        Case.step('boot to OS')
        Case.sleep(60)
        sut.press_power_button_short()
        Case.wait_and_expect("system power status = S0", 600, check_system_power_status, sut, SUT_STATUS.S0)
        Case.wait_and_expect(f'wait system back to {sut.default_os}', 60 * 60, sut.check_system_in_os)
        Case.sleep(60)

        Case.step('check without MCE error')
        ret, stdout, _ = sut.execute_shell_cmd(r'dmesg | grep -i MCE')
        Case.expect("no MCE error in dmesg log", "error" not in stdout)

        Case.sleep(60)


def clean_up(sut):
    default_cleanup(sut)


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
