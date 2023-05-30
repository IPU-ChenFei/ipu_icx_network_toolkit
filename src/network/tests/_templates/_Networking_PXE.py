
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'build pxe server environment in sut2 linux os',
    'download file from sut2 to sut1'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    proxy = ParameterParser.parse_parameter("proxy")
    if proxy:
        proxy = proxy.replace(',', ' ')
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("assign ip address")
    valos.ip_assign(conn)

    Case.step("build pxe server environment")
    pxe_file = "pxe_uefi_redhat.sh" if sutos == "redhat" else "pxe_uefi_centos.sh"
    sut2.upload_to_remote(os.path.join(valos.common_path, "tool", pxe_file), valos.tool_path)
    sut2.execute_shell_cmd('dos2unix {}/{}'.format(valos.tool_path, pxe_file))
    sut2.execute_shell_cmd("source {}/{} {} {}".format(valos.tool_path, pxe_file, conn.port2.ip, proxy))
    _, stdout, _ = sut2.execute_shell_cmd('systemctl status dhcpd.service')
    Case.expect('dhcpd service is active', 'Active: active (running)' in stdout)
    _, stdout, _ = sut2.execute_shell_cmd('systemctl status tftp.service')
    Case.expect('tftp service is active', 'Active: active (running)' in stdout)

    Case.step("enable server efi network")
    set_bios_knobs_step(sut1, *bios_knob('enable_efi_network'))

    Case.step("select boot device to download NBP file")
    mac = valos.get_mac_address(sut1, conn.port1.nic.id_in_os.get(sutos), 0)
    boot_nic = 'UEFI PXEv4 (MAC:{})'.format(mac.replace(':', '').upper())
    enter_path = ['Boot Manager Menu', boot_nic]
    my_os.reset_to_bios_menu(sut1)
    sut1.bios.bios_setup_enter_path(enter_path)

    retcode = sut1.bios.bios_log.search_for_keyword('NBP file downloaded successfully.', 600)
    Case.expect('wait for image file download succeessful', retcode)
    Case.sleep(10)

    Case.step("switch sut1 status to os")
    sut1.ac_off()
    Case.wait_and_expect("system power status = G3", 60, check_system_power_status, sut1, SUT_STATUS.G3)
    sut1.ac_on()
    Case.wait_and_expect("wait for sut1 status in os", 60 * 5, sut1.check_system_in_os)


def clean_up(sut):
    set_bios_knobs_step(sut, *bios_knob('disable_efi_network'))

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
