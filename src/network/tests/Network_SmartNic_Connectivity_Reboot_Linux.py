#from src.lib.toolkit.auto_api import *
#from sys import exit
#from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
#from src.mev.lib.mev import MEV, MEVOp
from src.network.lib import *

CASE_DESC = [
    # TODO
    'PI Networking Frtville connectivityReboot CentOS',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)

    try:
        boot_to(sut, sut.default_os)
        mev.general_bring_up()

        # Step1 - load driver, ping DHCP server and reboot for 5 times.
        sut.execute_shell_cmd('mkdir ConnetivityReboot_dmesg_log')
        for i in range(20):
            Case.step('Get IP from DHCP for XHC and ping from XHC to DHCP server')
            mev.pass_xhc_traffic()
            Case.expect('ping to DHCP client successfully.', MEVOp.ping_to_dhcp(mev.xhc, mode='ipv4'))
            sut.execute_shell_cmd(f'dmesg > /root/ConnetivityReboot_dmesg_log/dmesg_{i}')
            sut.execute_shell_cmd("dmesg -C")
            my_os.warm_reset_cycle_step(sut)
    except Exception as e:
        raise e
    finally:
        sut.download_to_local('/root/ConnetivityReboot_dmesg_log', LOG_PATH)
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
