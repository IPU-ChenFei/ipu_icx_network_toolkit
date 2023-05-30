from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp

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
        mev.general_bring_up()
        mev.execute_acc_cmd("modprobe vfio-platform-base", timeout=60)
        mev.execute_acc_cmd("modprobe vfio-platform", timeout=60)
        mev.execute_acc_cmd("echo vfio-platform > /sys/bus/platform/devices/2000000000.abe/driver_override")
        mev.execute_acc_cmd("echo 2000000000.abe > /sys/bus/platform/drivers_probe")
        mev.execute_acc_cmd("/usr/bin/abe", timeout=5, async_cmd=True)
        _, _, err = mev.execute_acc_cmd("/usr/bin/abe", timeout=5)
        Case.expect("Run ABE application successfully", "already running" in err)

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
