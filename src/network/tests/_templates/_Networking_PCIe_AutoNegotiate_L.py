from src.network.lib import *
CASE_DESC = [
    'this case is used  to check the E810 NIC ability to correctly negotiate the link speed (including link '
    'auto-negotiation and link parallel-detection) '
    'sut1: server\r\n'
    'sut2: client\r\n'
]


def check_speed(sut1, conn, srv, try_time=10):
    sut1.execute_shell_cmd("ping -c 5 {}".format(conn.port2.ip))
    code, out, err = sut1.execute_shell_cmd(f"ethtool {srv}")
    speed = str(log_check.scan_format("Speed: %s", out))
    if speed == "Unknown!":
        try_time = try_time - 1
        if try_time == 0:
            raise RuntimeError("check speed error")
        Case.sleep(10)
        check_speed(sut1, conn, srv, try_time)
    else:
        return speed


path = os.path.abspath(__file__)
project_path = path.split('src')[0]
file_path = r"{}src\network\lib\tool\advertise-code.txt".format(project_path)


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

    Case.step("Boot sut to linux os set ip address ")
    valos.ip_assign(conn)

    Case.step("get nic info")
    srv = valos.get_ether_name(sut1, conn.port1.nic.id_in_os.get(sutos), 0)

    Case.step("Check if auto-negotiation is supported on test nic port")
    code, out, err = sut1.execute_shell_cmd(f"ethtool {srv}")
    # "Supports auto-negotiation: Yes" should be in output, otherwise mark test fails
    res = log_check.find_lines("Supports auto-negotiation: Yes", out)
    Case.expect('"Supports auto-negotiation: Yes" should be in output, otherwise mark test fails', len(res) != 0)

    # enable client auto negotiation
    Case.step("Enable auto negotiation for test nic port (this always be the default option)")
    code, out, err = sut2.execute_shell_cmd(f"ethtool {srv}")
    res = log_check.find_lines("Auto-negotiation: off", out)
    # off
    if len(res) != 0:
        code, out, err = sut2.execute_shell_cmd(f"ethtool -s {srv} autoneg on")
        Case.expect('"execute command successful! ', err == "")
    code, out, err = sut2.execute_shell_cmd(f"ethtool {srv}")
    res = log_check.find_lines("Auto-negotiation: on", out)
    Case.expect('"Auto-neogtiation: on" should be shown in output', len(res) != 0)

    Case.step("Check test nic port works at the fatest supported speed & full duplex")
    speed = check_speed(sut1, conn, srv)
    Case.expect(f"Auto negotiation shows the fatest speed & full duplex [{speed}]", speed != "")

    Case.step("Link Parallel Detection Check")
    code, out, err = sut1.execute_shell_cmd(f"ethtool {srv}")
    test_speed = log_check.scan_format("Advertised link modes:  %s %s %s %s %s %s ", out)
    speed_list = []
    for tmp in test_speed:
        if re.search("[0-9]", tmp) and "Half" not in tmp:
            speed_list.append(tmp)
    with open(file_path, "r") as file:
        file_str = file.read()

    for speed in speed_list:
        speed = speed.replace("/", " ")
        Case.step(f"=============== {speed} ==================")
        # 0x80000000000
        speed_code = log_check.find_lines(speed, file_str)[0].split(speed)[0].strip()
        sut1.execute_shell_cmd(f"ethtool -s {srv} advertise {speed_code}")
        current_speed = check_speed(sut1, conn, srv)
        # get number value For compare
        speed = re.search(r"[0-9]+", speed).group()
        current_speed = re.search(r"[0-9]+", current_speed).group()
        Case.expect("Speed output shows correct value", current_speed == speed)


def clean_up(sut, sut2):
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
        # clean_up(sut, sut2)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
