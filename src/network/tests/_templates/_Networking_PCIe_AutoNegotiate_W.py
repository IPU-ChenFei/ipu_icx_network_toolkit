from src.network.lib import *
CASE_DESC = [
    'this case is used  to check the E810 NIC ability to correctly negotiate the link speed '
    '(including link auto-negotiation and link parallel-detection)'
]

def Link_Speed_Deal(LinkSpeedList):
    #LinkSpeed = ['Auto Negotiation', '1.0 Gbps Full Duplex', '10 Gbps Full Duplex', '25 Gbps Full Duplex']
    LinkSpeed_1G_List = ['Auto Negotiation', '100 Mbps Full Duplex', '1.0 Gbps Full Duplex']
    LinkSpeed_10G_List = ['Auto Negotiation', '1.0 Gbps Full Duplex', '10 Gbps Full Duplex']
    LinkSpeed_25G_List = ['Auto Negotiation', '10 Gbps Full Duplex', '25 Gbps Full Duplex']
    LinkSpeed_40G_List = ['Auto Negotiation', '10 Gbps Full Duplex', '40 Gbps Full Duplex']
    LinkSpeed_100G_List = ['Auto Negotiation', '25 Gbps Full Duplex', '100 Gbps Full Duplex']
    len = LinkSpeedList.__len__()
    if LinkSpeedList[len-1] == LinkSpeed_1G_List[2]:
        return LinkSpeed_1G_List
    elif LinkSpeedList[len-1] == LinkSpeed_10G_List[2]:
        return LinkSpeed_10G_List
    elif LinkSpeedList[len-1] == LinkSpeed_25G_List[2]:
        return LinkSpeed_25G_List
    elif LinkSpeedList[len-1] == LinkSpeed_40G_List[2]:
        return LinkSpeed_40G_List
    elif LinkSpeedList[len-1] == LinkSpeed_100G_List[2]:
        return LinkSpeed_100G_List
    else:
        return LinkSpeedList


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

    Case.step("Boot sut to windows os set ip address ")
    valos.ip_assign(conn)

    Case.step("Check if auto-negotiation is supported on test nic port")
    sut1_pci_type = conn.port1.nic.id_in_os.get(sutos)
    nic = valos.get_ether_name(sut1, sut1_pci_type, 0)
    sut2_pci_type = conn.port1.nic.id_in_os.get(sutos)
    nic2 = valos.get_ether_name(sut2, sut2_pci_type, 0)
    res = sut1.execute_shell_cmd(
        f'Get-NetAdapterAdvancedProperty -Name "{nic}" -DisplayName "Speed & Duplex" | Select '
        f'-Expand ValidDisplayValues', powershell=True)[1]
    #LinkSpeed = res.splitlines()
    LinkSpeed = Link_Speed_Deal(res.splitlines())
    Case.expect(f"get speed {res} pass", res != '')

    Case.step("Enable auto negotiation")
    ret = sut1.execute_shell_cmd(
        f'Set-NetAdapterAdvancedProperty -Name "{nic}" -DisplayName "Speed & Duplex" '
        f'-DisplayValue "Auto Negotiation"', powershell=True)[0]
    Case.expect("set ethernet enable pass", ret == 0)

    Case.step("Check test nic port works at the fatest supported speed & full duplex")
    ret, res, err = sut1.execute_shell_cmd('Get-NetAdapter | select Name, LinkSpeed, FullDuplex', powershell=True)
    Case.expect(f"show the linkspeed fullduplex {res}", res != '')

    Case.step("change te speed")
    for speed in LinkSpeed:
        sut1.execute_shell_cmd(
            f'Set-NetAdapterAdvancedProperty -Name "{nic}" -DisplayName "Speed & Duplex" -DisplayValue "{speed}"',
            powershell=True)
        ret, res, error = sut1.execute_shell_cmd(f'Get-NetAdapterAdvancedProperty -Name "{nic}" '
                                                 f'-DisplayName "Speed & Duplex"', powershell=True)
        res = log_check.find_lines(speed, res)
        Case.expect(f"show the change speed: {res}", res != 0)
        sut2.execute_shell_cmd(
            f'Set-NetAdapterAdvancedProperty -Name "{nic2}" -DisplayName "Speed & Duplex" -DisplayValue "{speed}"',
            powershell=True)
        Case.sleep(5)
        ret = sut1.execute_shell_cmd("ping -n 20 {}".format(conn.port2.ip))[0]
        Case.expect(f"change speed {speed} ping is ok", ret == 0)


def clean_up(sut):
    #pass
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
    my_os = OperationSystem[sut.default_os]
    # my_os = OperationSystem[OS.get_os_family(sut.default_os)]

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
