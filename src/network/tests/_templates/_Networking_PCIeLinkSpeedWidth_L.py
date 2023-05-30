from src.network.lib import *
CASE_DESC=[
    'connect sut1 network port to sut2 network port cable',
    'check mellanox speed and width'
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

    Case.step("Change sut1 and sut2 network interface mode to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH")
    valos.switch_infiniband_mode(sut2, "ETH")

    Case.step("set mellanox card ipv4")
    valos.ip_assign(conn)

    Case.step("check mellanox speed and width")
    sut_pci_type = conn.port1.nic.id_in_os.get(sutos)
    stdout = sut.execute_shell_cmd("lspci | grep -i %s | awk '{print $1}'" % sut_pci_type)[1]
    bus = stdout.splitlines()[0].strip()
    speed = sut.execute_shell_cmd("cat /sys/bus/pci/devices/0000:{}/max_link_speed".format(bus))[1]
    width = sut.execute_shell_cmd("cat /sys/bus/pci/devices/0000:{}/max_link_width".format(bus))[1]

    speed = re.search('\d+', speed).group()
    Case.expect("compare mellanox speed", speed == conn.port1.nic.type.speed)
    width = re.search('\d+', width).group()
    Case.expect("compare mellanox width", width == conn.port1.nic.type.width)


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