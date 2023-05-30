
from src.network.lib import *
CASE_DESC=[
    'connect sut1 network port to sut2 network port cable',
    'set ipv4 and ipv6 address for Onboard NIC and ping successful',
    'running iwvss io stress test'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn_v4 = ParameterParser.parse_parameter("conn4")
    conn_v6 = ParameterParser.parse_parameter("conn6")
    pkg = ParameterParser.parse_parameter("tool")
    conf = ParameterParser.parse_parameter("conf")
    flow = ParameterParser.parse_parameter("flow")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn4 = nic_config(sut1, sut2, conn_v4)
    conn6 = nic_config(sut1, sut2, conn_v6)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("Change sut1 and sut2 network interface mode to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH", "windows")
    valos.switch_infiniband_mode(sut2, "ETH", "windows")

    Case.step("set ipv4")
    valos.ip_assign(conn4)

    Case.step("set ipv6")
    valos.ipv6_enable = True
    valos.ip_assign(conn6)

    Case.step("running ixvss stress test")
    valos.ixvss_stress(10, pkg, conf, flow, conn4)


def clean_up(sut):
    from dtaf_core.lib.tklib.steps_lib import cleanup
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