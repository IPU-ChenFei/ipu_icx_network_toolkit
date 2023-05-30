from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'set ipv4 address for NIC and ping ipv4 successful and disable SUT1 NIC ping with SUT2 failed,'
    'enable SUT1 NIC and ping ipv4 successful'
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

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("disable ipv4")
    sut1_pci_type = conn.port1.nic.id_in_os.get(sutos)
    nic = valos.get_ether_name(sut1, sut1_pci_type, 0)
    for i in range(3):
        try:
            #sut1.ssh_connection(60, sut1.check_ssh_status)
            ret = sut1.execute_shell_cmd('Disable-NetAdapter -Name "{}" -Confirm:$False'.format(nic), powershell=True)
            Case.expect("disable ipv4", ret[2] == '')
            time.sleep(5)
            ret, out, err = sut1.execute_shell_cmd("ping -n 6 {}".format(conn.port2.ip))
            lost_data = re.search(r"\((\d+)%\sloss\)", out)
            Case.expect("ping failed", int(lost_data.group(1)) == 100)

            Case.step("enable ipv4")
            #sut1.ssh_connection(60, sut1.check_ssh_status)
            ret = sut1.execute_shell_cmd('Enable-NetAdapter -Name "{}" -Confirm:$False'.format(nic), powershell=True)
            Case.expect("enable ipv4", ret[2] == '')
            time.sleep(30)
            ret = sut1.execute_shell_cmd("ping -n 20 {}".format(conn.port2.ip))
            Case.expect("ping successful", ret[0] == 0)
        except Exception as e:
            Case.step("Case Error restore env")
            #sut1.ssh_connection(60, sut1.check_ssh_status)
            ret = sut1.execute_shell_cmd('Enable-NetAdapter -Name "{}" -Confirm:$False'.format(nic), powershell=True)
            time.sleep(5)
            raise
        finally:
            Case.step("Case Over")


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