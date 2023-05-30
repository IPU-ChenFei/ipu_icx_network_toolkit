
from src.network.lib import *
CASE_DESC = [
    'connect sut1 nic port to sut2 nic port cable',
    'set sut1 as a server and sut2 as a client',
    'running wol.py in client to wakeup server'
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
    boot_to(sut1, SUT_STATUS.S0.UEFI_SHELL)
    sut1.restore_bios_defaults_xmlcli(SUT_STATUS.S0.UEFI_SHELL)
    UefiShell.reset_to_os(sut1)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("enable wakeup setting")
    set_bios_knobs_step(sut1, *bios_knob('enable_wol_knob_setting_xmlcli'))
    my_os.reset_cycle_step(sut1)

    flag = conn.port1.nic.id_in_os.get(sutos)
    srv_mac = valos.get_mac_address(sut1, flag, 0)
    srv_ip = re.search(r"\d+\.\d+\.\d+", conn.port1.ip).group() + ".255"
    eth_name = valos.get_ether_name(sut1, flag, 0)
    sut1.execute_shell_cmd("ethtool -s {} wol g".format(eth_name))

    Case.step("dc off server")
    my_os.shutdown(sut1)
    sut1.wait_for_power_status(SUT_STATUS.S5, 20)

    Case.step("wakeup server")
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    sut2.upload_to_remote(os.path.join(valos.common_path, "tool", "wol.py"), valos.tool_path)
    ret_code = sut2.execute_shell_cmd("python {}/wol.py {} {}".format(valos.tool_path, srv_mac, srv_ip))[0]
    Case.expect("execute wol.py file command", ret_code == 0)
    ret = sut1.wait_for_power_status(SUT_STATUS.S0, 600)
    Case.expect('sut1 enter power status S0', ret)
    Case.wait_and_expect("wait for sut1 status in os", 60 * 5, sut1.check_system_in_os)


def clean_up(sut):
    set_bios_knobs_step(sut, *bios_knob('disable_wol_knob_setting_xmlcli'))

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
