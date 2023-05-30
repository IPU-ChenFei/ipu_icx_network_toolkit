from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp


CASE_DESC = [
    # TODO
    'Mev_System_Tests_Platform_System_Boot_Xeon',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # Prepare steps - call predefined steps
    mev = MEV(sut)
    try:
        boot_to(sut, sut.default_os)
        mev.general_bring_up(sut)

        # Step1 - Check with systemctl is system running
        Case.step('Check with systemctl is system running')
        return_code, stdout, stderr = sut.execute_shell_cmd('systemctl is-system-running --wait', 30)
        Case.expect('check returns the value is degraded or running',
                    'degraded' in stdout or 'running' in stdout or 'starting' in stdout)

        # Step2 - Check list units for systemctl
        Case.step('Check list units for systemctl')
        return_code, stdout, stderr = sut.execute_shell_cmd('systemctl list-units | grep "Basic System" | tr -s " "', 30)
        Case.expect('Check returns the value is basic.target loaded active active Basic System',
                    'basic.target loaded active active Basic System' in stdout)
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

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
