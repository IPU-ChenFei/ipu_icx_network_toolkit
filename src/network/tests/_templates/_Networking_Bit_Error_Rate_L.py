
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'Test Infiniband adapter and cable quality similar to IBTA standards'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    IB_READ_BW = 6200.0
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("bios setting")
    set_bios_knobs_step(sut1, *bios_knob('enable_SpeedStep_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('enable_SpeedStep_xmlcli'))

    Case.step("Change sut1 and sut2 network interface mode to IB mode")
    valos.switch_infiniband_mode(sut1, "IB")
    valos.switch_infiniband_mode(sut2, "IB")

    Case.step("set mellanox card IB ip")
    valos.ip_assign(conn)

    Case.step("create OpenSM instance for 2 SUT")
    _, stdout, _ = sut1.execute_shell_cmd('ibstat | grep "State|Port" -E')
    flag = False
    port_id = ""
    for line in stdout.splitlines():
        if re.search("State: Active", line):
            flag = True
            continue
        if flag:
            port_id = re.search("Port GUID:\s(\w+)", line).group(1)
            flag = False
    ret = sut1.execute_shell_cmd('opensm -g {}'.format(port_id))
    if not ret[0] == 0:
        Case.expect("create opensm instance", "Exiting SM" in ret[1])
    ret = sut2.execute_shell_cmd('opensm -g {}'.format(port_id))
    if not ret[0] == 0:
        Case.expect("create opensm instance", "Exiting SM" in ret[1])

    Case.step("clear perfquery")
    sut1.execute_shell_cmd('perfquery -R')
    sut2.execute_shell_cmd('perfquery -R')

    Case.step("run benchmark")
    sut2.execute_shell_cmd_async("ib_read_bw", cwd="/usr/bin", timeout=60)
    stdout = sut1.execute_shell_cmd("ib_read_bw {}".format(conn.port2.ip), cwd="/usr/bin")[1]
    for line in stdout.splitlines():
        ret = re.search("\d+\s+\d+\s+", line)
        if ret:
            read_val = line.split()[3]
            Case.expect("compare ib read bw value", float(read_val) > IB_READ_BW * 0.9)

    Case.step("run perfquery")
    stdout = sut1.execute_shell_cmd('perfquery')[1]
    for line in stdout.splitlines():
        ret = re.search('.*Error.*\.+(\d+)', line)
        if ret:
            Case.expect("run perfquery no errors", int(ret.group(1).strip()) == 0)

    stdout = sut2.execute_shell_cmd('perfquery')[1]
    for line in stdout.splitlines():
        ret = re.search('.*Error.*\.+(\d+)', line)
        if ret:
            Case.expect("run perfquery no errors", int(ret.group(1).strip()) == 0)

    Case.step("restore SUT1 and SUT2 network interface back to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH")
    valos.switch_infiniband_mode(sut2, "ETH")


def clean_up(sut, sut2):
    set_bios_knobs_step(sut, *bios_knob('disable_SpeedStep_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('disable_SpeedStep_xmlcli'))

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
    sut2 = get_sut_list()[1]
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)
    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut, sut2)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
