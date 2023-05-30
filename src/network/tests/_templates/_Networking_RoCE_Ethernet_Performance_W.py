
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'set Mellanox card to ETH mode',
    'check RoCE Performance output'
]


def __enable_rdma(sut):
    stdout = sut.execute_shell_cmd("get-NetAdapterRdma -Name *", powershell=True)[1]
    nic_list = []
    for line in stdout.splitlines():
        nicname = re.search("(Ethernet.*)Mellanox", line)
        if nicname:
            nic_list.append(nicname.group(1).strip())
    for name in nic_list:
        ret = sut.execute_shell_cmd('Enable-NetAdapterRdma -Name "{}"'.format(name), powershell=True)[2]
        Case.expect("enable RDMA", ret == '')


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

    Case.step("Change sut1 and sut2 network interface mode to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH", "windows")
    valos.switch_infiniband_mode(sut2, "ETH", "windows")

    Case.step("set mellanox ipv4")
    valos.ip_assign(conn)

    Case.step("enable RDMA")
    __enable_rdma(sut1)
    __enable_rdma(sut2)

    Case.step("running MLNX_WinOF2 tools")
    tool = "C:\\\"Program Files\"\\Mellanox\\MLNX_WinOF2\\\"Performance Tools\""
    Case.step("test nd_read_bw")
    sut1.execute_shell_cmd_async("{}\\nd_read_bw -a -S {}".format(tool, conn.port1.ip))
    retcode, rbw, _ = sut2.execute_shell_cmd("{}\\nd_read_bw -a -C {}".format(tool, conn.port1.ip), timeout=600)
    Case.expect("execute command to read bw", retcode == 0)

    Case.step("test nd_send_bw")
    sut1.execute_shell_cmd_async("{}\\nd_send_bw -a -S {}".format(tool, conn.port1.ip))
    retcode, sbw, _ = sut2.execute_shell_cmd("{}\\nd_send_bw -a -C {}".format(tool, conn.port1.ip), timeout=600)
    Case.expect("execute command to send bw", retcode == 0)

    Case.step("test nd_write_bw")
    sut1.execute_shell_cmd_async("{}\\nd_write_bw -a -S {}".format(tool, conn.port1.ip))
    retcode, wbw, _ = sut2.execute_shell_cmd("{}\\nd_write_bw -a -C {}".format(tool, conn.port1.ip), timeout=600)
    Case.expect("execute command to write bw", retcode == 0)

    Case.step("test nd_read_lat")
    sut1.execute_shell_cmd_async("{}\\nd_read_lat -a -S {}".format(tool, conn.port1.ip))
    retcode, rlab, _ = sut2.execute_shell_cmd("{}\\nd_read_lat -a -C {}".format(tool, conn.port1.ip), timeout=600)
    Case.expect("execute command to read lat", retcode == 0)

    Case.step("test nd_send_lat")
    sut1.execute_shell_cmd_async("{}\\nd_send_lat -a -S {}".format(tool, conn.port1.ip))
    retcode, slat, _ = sut2.execute_shell_cmd("{}\\nd_send_lat -a -C {}".format(tool, conn.port1.ip), timeout=600)
    Case.expect("execute command to send lat", retcode == 0)

    Case.step("test nd_write_lat")
    sut1.execute_shell_cmd_async("{}\\nd_write_lat -a -S {}".format(tool, conn.port1.ip))
    retcode, wlat, _ = sut2.execute_shell_cmd("{}\\nd_write_lat -a -C {}".format(tool, conn.port1.ip), timeout=600)
    Case.expect("execute command to write lat", retcode == 0)


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
