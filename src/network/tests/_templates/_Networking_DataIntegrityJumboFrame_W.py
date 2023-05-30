
from src.network.lib import *
CASE_DESC=[
    'connect sut1 network port to sut2 network port cable',
    'enable jumbo frame'
    'set ipv4 address for Onboard nic',
    'running iwvss stress test'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    pkg = ParameterParser.parse_parameter("tool")
    conf = ParameterParser.parse_parameter("conf")
    flow = ParameterParser.parse_parameter("flow")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("enable jumbo frame")
    nic_name = None
    stdout = sut1.execute_shell_cmd("wmic path win32_networkadapter get Description,NetConnectionID,NetEnabled")[1]
    for line in stdout.splitlines():
        ret = re.search("{}.*(Ethernet.*)TRUE".format(conn.port2.nic.id_in_os.get(sutos)), line)
        if ret:
            nic_name = ret.group(1).strip()
    Case.expect("get adapter name {}".format(nic_name), nic_name)

    stderr = sut1.execute_shell_cmd(r'Set-NetAdapterAdvancedProperty -Name "{}" -DisplayName "Jumbo Packet" -DisplayValue "9014 Bytes"'.format(nic_name), powershell=True)[2]
    Case.expect("enable sut1 jumbo frame", stderr == '')
    my_os.warm_reset_cycle_step(sut1)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("sut1 and sut2 ping each other")
    valos.ip_assign(conn)

    Case.step("running ixvss stress test")
    valos.ixvss_stress(10, pkg, conf, flow, conn)


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