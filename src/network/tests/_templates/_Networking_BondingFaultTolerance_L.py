from src.network.lib import *


CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'bond port1 and port2 for both nic ping successful',
    'ifdown one of nic port still ping successful'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conns = muti_nic_config(sut1, sut2)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    try:
        Case.step("del old bond if case failed")
        sut_pci_type = conns[0].port1.nic.id_in_os.get(sutos)
        sut1_main_nic = valos.get_ether_name(conns[0].port1.sut, sut_pci_type, 0)
        sut1_sub_nic = valos.get_ether_name(conns[0].port1.sut, sut_pci_type, 1)
        sut1.execute_shell_cmd("nmcli con delete bond0")
        sut1.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut1_main_nic))
        sut1.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut1_sub_nic))
        sut2_main_nic = valos.get_ether_name(conns[0].port2.sut, sut_pci_type, 0)
        sut2_sub_nic = valos.get_ether_name(conns[0].port2.sut, sut_pci_type, 1)
        sut2.execute_shell_cmd("nmcli con delete bond1")
        sut2.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut2_main_nic))
        sut2.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut2_sub_nic))

        Case.step("set ipv4")
        valos.ip_assign(*conns)

        Case.step("set bond")
        bond_ip = conns[0].port1.ip + '0'
        bond_ip2 = conns[1].port1.ip + '0'

        Case.step("create sut1 bond0 and config IP")
        ret = sut1.execute_shell_cmd("nmcli con add type bond con-name bond0 ifname bond0 mode active-backup")
        Case.expect("add bond0", ret[0] == 0)
        ret = sut1.execute_shell_cmd("nmcli con add type bond-slave ifname {} master bond0".format(sut1_main_nic))
        Case.expect("add bond-slave {}".format(sut1_main_nic), ret[0] == 0)
        ret = sut1.execute_shell_cmd("nmcli con up bond-slave-{}".format(sut1_main_nic))
        Case.expect("up bond-slave-{}".format(sut1_main_nic), ret[0] == 0)
        Case.sleep(5)
        ret = sut1.execute_shell_cmd("nmcli con add type bond-slave ifname {} master bond0".format(sut1_sub_nic))
        Case.expect("add bond0 bond-slave {}".format(sut1_sub_nic), ret[0] == 0)
        ret = sut1.execute_shell_cmd("nmcli con up bond-slave-{}".format(sut1_sub_nic))
        Case.expect("up bond-slave-{}".format(sut1_sub_nic), ret[0] == 0)
        Case.sleep(5)
        ret = sut1.execute_shell_cmd("nmcli con modify bond0 connection.autoconnect yes")
        Case.expect("open bond0 autoconnect", ret[0] == 0)
        ret = sut1.execute_shell_cmd("nmcli con modify bond0 ipv4.address {}/24".format(bond_ip))
        Case.expect("add ip address for bond0", ret[0] == 0)
        ret = sut1.execute_shell_cmd("nmcli con modify bond0 ipv4.method manual")
        Case.expect("set bond0 ipv4 to manual", ret[0] == 0)
        ret = sut1.execute_shell_cmd("nmcli con up bond0")
        Case.expect("up bond0", ret[0] == 0)
        Case.sleep(5)

        Case.step("create sut2 bond1 and config IP")
        ret = sut2.execute_shell_cmd("nmcli con add type bond con-name bond1 ifname bond1 mode active-backup")
        Case.expect("add bond1", ret[0] == 0)
        ret = sut2.execute_shell_cmd("nmcli con add type bond-slave ifname {} master bond1".format(sut2_main_nic))
        Case.expect("add bond-slave {}".format(sut2_main_nic), ret[0] == 0)
        ret = sut2.execute_shell_cmd("nmcli con up bond-slave-{}".format(sut2_main_nic))
        Case.expect("up bond-slave-{}".format(sut2_main_nic), ret[0] == 0)
        Case.sleep(5)
        ret = sut2.execute_shell_cmd("nmcli con add type bond-slave ifname {} master bond1".format(sut2_sub_nic))
        Case.expect("add bond1 bond-slave {}".format(sut2_sub_nic), ret[0] == 0)
        ret = sut2.execute_shell_cmd("nmcli con up bond-slave-{}".format(sut2_sub_nic))
        Case.expect("up bond-slave-{}".format(sut2_sub_nic), ret[0] == 0)
        Case.sleep(5)
        ret = sut2.execute_shell_cmd("nmcli con modify bond1 connection.autoconnect yes")
        Case.expect("open bond1 autoconnect", ret[0] == 0)
        ret = sut2.execute_shell_cmd("nmcli con modify bond1 ipv4.address {}/24".format(bond_ip2))
        Case.expect("add ip address for bond1", ret[0] == 0)
        ret = sut2.execute_shell_cmd("nmcli con modify bond1 ipv4.method manual")
        Case.expect("set bond1 ipv4 to manual", ret[0] == 0)
        ret = sut2.execute_shell_cmd("nmcli con up bond1")
        Case.expect("up bond1", ret[0] == 0)
        Case.sleep(5)

        Case.step("bond ping")
        ret = sut2.execute_shell_cmd(valos.ping.format(bond_ip))
        Case.expect("sut2 ping sut1 bond0", valos.ping_result_check(ret[1]))
        # test ping for down main nic & up sub nic
        ret = sut1.execute_shell_cmd("ifconfig {} down & ifconfig {} up".format(sut1_main_nic, sut1_sub_nic))
        Case.expect("down nic port {} and up nic port {}".format(sut1_main_nic, sut1_sub_nic), ret[0] == 0)
        ret = sut2.execute_shell_cmd("ifconfig {} down & ifconfig {} up".format(sut2_main_nic, sut2_sub_nic))
        Case.expect("down nic port {} and up nic port {}".format(sut2_main_nic, sut2_sub_nic), ret[0] == 0)
        Case.sleep(10)
        ret = sut2.execute_shell_cmd(valos.ping.format(bond_ip))
        Case.expect("sut2 ping sut1 bond0", valos.ping_result_check(ret[1]))
        # test ping for up main nic & down sub nic
        ret = sut1.execute_shell_cmd("ifconfig {} up & ifconfig {} down".format(sut1_main_nic, sut1_sub_nic))
        Case.expect("down nic port {} and up nic port {}".format(sut1_main_nic, sut1_sub_nic), ret[0] == 0)
        ret = sut2.execute_shell_cmd("ifconfig {} up & ifconfig {} down".format(sut2_main_nic, sut2_sub_nic))
        Case.expect("down nic port {} and up nic port {}".format(sut2_main_nic, sut2_sub_nic), ret[0] == 0)
        Case.sleep(10)
        ret = sut2.execute_shell_cmd(valos.ping.format(bond_ip))
        Case.expect("sut2 ping sut1 bond0", valos.ping_result_check(ret[1]))

        Case.step("delete bond")
    except Exception as e:
        sut1.execute_shell_cmd("nmcli con delete bond0")
        sut1.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut1_main_nic))
        sut1.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut1_sub_nic))
        sut2.execute_shell_cmd("nmcli con delete bond1")
        sut2.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut2_main_nic))
        sut2.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut2_sub_nic))

        # delete orignial port config
        sut1.execute_shell_cmd("nmcli con delete {}".format(sut1_main_nic))
        sut1.execute_shell_cmd("nmcli con delete {}".format(sut1_sub_nic))
        sut2.execute_shell_cmd("nmcli con delete {}".format(sut2_main_nic))
        sut2.execute_shell_cmd("nmcli con delete {}".format(sut2_sub_nic))
        raise err
    finally:
        sut1.execute_shell_cmd("nmcli con delete bond0")
        sut1.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut1_main_nic))
        sut1.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut1_sub_nic))
        sut2.execute_shell_cmd("nmcli con delete bond1")
        sut2.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut2_main_nic))
        sut2.execute_shell_cmd("nmcli con delete bond-slave-{}".format(sut2_sub_nic))

        # delete orignial port config
        sut1.execute_shell_cmd("nmcli con delete {}".format(sut1_main_nic))
        sut1.execute_shell_cmd("nmcli con delete {}".format(sut1_sub_nic))
        sut2.execute_shell_cmd("nmcli con delete {}".format(sut2_main_nic))
        sut2.execute_shell_cmd("nmcli con delete {}".format(sut2_sub_nic))


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
