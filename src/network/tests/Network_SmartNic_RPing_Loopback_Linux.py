#from src.lib.toolkit.auto_api import *
#from sys import exit
#from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
#from src.mev.lib.mev import MEV, MEVOp
from src.network.lib import *

CASE_DESC = [
    # TODO
    'Basic LAN IPv6 Ping with Link Partner',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        boot_to(sut, sut.default_os)

        # Step1 Load RDMA env
        MEVOp.rdma_common_prepare_step(mev)

        # Step2 Setup loopback mode
        MEVOp.load_loop_back_env(mev)

        # Step3 Assigin IP for each namespace
        sut.execute_shell_cmd("ip netns exec ns0 ip link set dev ipvl0 up")
        sut.execute_shell_cmd("ip netns exec ns0 ip link set dev lo up")
        sut.execute_shell_cmd("ip netns exec ns0 ip -4 addr add 127.0.0.1 dev lo")
        sut.execute_shell_cmd("ip netns exec ns0 ip -4 addr add 200.0.0.1/24 dev ipvl0")

        sut.execute_shell_cmd("ip netns exec ns1 ip link set dev ipvl1 up")
        sut.execute_shell_cmd("ip netns exec ns1 ip link set dev lo up")
        sut.execute_shell_cmd("ip netns exec ns1 ip -4 addr add 127.0.0.1 dev lo")
        sut.execute_shell_cmd("ip netns exec ns1 ip -4 addr add 200.0.0.2/24 dev ipvl1")

        sut.execute_shell_cmd_async("ip netns exec ns1 ucmatose -b 200.0.0.2 -c 2 -C 10 -S 1024")
        ret, _, _ = sut.execute_shell_cmd("ip netns exec ns0 ucmatose -s 200.0.0.2 -c 2 -C 10 -S 1024")
        Case.expect('ucmatose finish successfully', ret == 0)
    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


def clean_up(mev: MEV):
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
