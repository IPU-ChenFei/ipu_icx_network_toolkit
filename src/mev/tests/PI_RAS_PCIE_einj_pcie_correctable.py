from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp
from src.configuration.config.bios.egs_bios import ras_knobs
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step


CASE_DESC = [
    # TODO
    'case name here',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        # TODO, replace these with your own steps
        # Prepare steps - call predefined steps
        boot_to(sut, sut.default_os)
        changed = set_bios_knobs_step(sut, *ras_knobs)
        if changed:
            my_os.g3_cycle_step(sut)
        # mev.general_bring_up()

        # Step1 -Clear dmesg and inject error
        Case.step('Clear dmesg and inject error')
        sut.execute_shell_cmd('dmesg -C')
        sut.execute_shell_cmd('modprobe einj')
        ret,_,_ = sut.execute_shell_cmd('echo 0x40 > error_type', cwd='/sys/kernel/debug/apei/einj')
        Case.expect('check cmd', ret == 0)
        sut.execute_shell_cmd('echo 0x0 > param1', cwd='/sys/kernel/debug/apei/einj')
        sut.execute_shell_cmd('echo 0 > param4', cwd='/sys/kernel/debug/apei/einj')
        sut.execute_shell_cmd('echo 0x4 > flags', cwd='/sys/kernel/debug/apei/einj')
        sut.execute_shell_cmd('echo 0 > notrigger', cwd='/sys/kernel/debug/apei/einj')
        sut.execute_shell_cmd('echo 1 > error_inject', cwd='/sys/kernel/debug/apei/einj')
        Case.sleep(10)

        # Step2 -Check dmesg to see if the error injected successfully
        Case.step('Check dmesg to see if the error injected successfully')

        ret_1, stdout, _ = sut.execute_shell_cmd('dmesg')
        Case.expect('Check error', 'Error 0, type: corrected' in stdout)
    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


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
