# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016909522',
    'Verify the SUT can warm rest'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)

    for i in range(10):
        logger.info(f'start No.{i} warm rest cycle')

        Case.step('clear dmesg before warm rest')
        ret, _, _ = sut.execute_shell_cmd('dmesg -C')
        Case.expect('clear dmesg successfully', ret == 0)

        my_os.warm_reset_cycle_step(sut)

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
