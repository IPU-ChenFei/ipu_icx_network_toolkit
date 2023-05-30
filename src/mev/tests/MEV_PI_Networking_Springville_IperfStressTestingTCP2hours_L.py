from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEVConn, MEVOp
from src.lib.toolkit.infra.sut import get_sut_list


CASE_DESC = [
    # TODO
    'PI_Networking_Springville_LperfStressTestingTCP2Hours_L',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut_list, my_os):
    sut1, sut2 = sut_list
    conn = MEVConn(sut1, sut2)
    mev1 = conn.port1
    mev2 = conn.port2
    try:
        boot_to(sut1, sut1.default_os)
        boot_to(sut2, sut2.default_os)
        conn.bring_up()
        conn.connect()

        # IMC 801
        mev1.pass_xhc_traffic()
        mev2.pass_xhc_traffic()
        sut1.execute_shell_cmd(f"ip a a 10.29.2.10/24 dev {mev1.xhc.eth_name}")
        sut2.execute_shell_cmd(f"ip a a 10.29.2.11/24 dev {mev2.xhc.eth_name}")

        # Iperf performance test
        Case.step('Get IP for 2 sut and do the iperf 3')
        MEVOp.iperf3_stress(duration=7200, client=mev2.xhc, servers=[mev1.xhc], thread_num=4)
    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(conn)


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
    sut_list = get_sut_list()
    sut = sut_list[0]
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut_list, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
