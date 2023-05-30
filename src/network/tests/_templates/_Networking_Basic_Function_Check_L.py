

from src.network.lib import *
CASE_DESC=[
    'connect sut1 mellanox nic port to sut2 mellanox nic port cable',
    'set sut1 as a server and sut2 as a client',
    'verify Ethernet mode functionallity of Infiniband IOM'
    'need use MCX556A-ECUT/MCX556A-EDAT/MCX556A-ECAT/MCX555A-ECAT mellanox card'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("Change SUT1 and SUT2 network interface back to IB mode")
    valos.switch_infiniband_mode(sut1, "IB")
    valos.switch_infiniband_mode(sut2, "IB")

    Case.step("Close SUT1 and SUT2 firewall")
    close_firewall = "systemctl start opensm & systemctl stop firewalld.service & systemctl disable firewalld.service"
    retcode = sut1.execute_shell_cmd(close_firewall)[0]
    Case.expect("create opensm instance and close sut1 firewalld", retcode == 0)
    retcode = sut2.execute_shell_cmd(close_firewall)[0]
    Case.expect("create opensm instance and close sut2 firewalld", retcode == 0)

    Case.step("Set SUT ip")
    valos.ip_assign(conn)

    Case.step("restore SUT1 and SUT2 network interface back to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH")
    valos.switch_infiniband_mode(sut2, "ETH")


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