from src.network.lib.dpdk.dpdk_common import *
from src.network.lib import *
CASE_DESC = [
    "this test is to verify dpdk functionality with vlan"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    tool = ParameterParser.parse_parameter("tool")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)
    Nic_Type = conn.port1.nic.id_in_os[sutos]

    Case.prepare("prepare OS")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    try:
        Case.step("set pci device ipv4")
        valos.ip_assign(conn)

        Case.step("upload dpdk python file")
        upload_dpdk_file(sut1)
        upload_dpdk_file(sut2)

        Case.step("get nic info")
        sut1_eth1_name = valos.get_ether_name(sut1, conn.port1.nic.id_in_os.get(sutos), 0)
        sut1_eth2_name = valos.get_ether_name(sut1, conn.port1.nic.id_in_os.get(sutos), 1)
        sut1_mac1_name = valos.get_mac_address(sut1, conn.port1.nic.id_in_os.get(sutos), 0)
        sut2_eth1_name = valos.get_ether_name(sut2, conn.port2.nic.id_in_os.get(sutos), 0)
        sut2_eth2_name = valos.get_ether_name(sut2, conn.port2.nic.id_in_os.get(sutos), 1)

        Case.step("set sut1 and sut2 environment")
        mtu_dpdk(sut1, sut1_eth1_name, sut1_eth2_name)
        mtu_dpdk(sut2, sut2_eth1_name, sut2_eth2_name)
        ret = sut1.execute_shell_cmd(MODPROBE_VFIO)[0]
        Case.expect("modprobe vfio successfully", ret == 0)
        sut1_id1, sut1_id2 = bind_dpdk(sut1, sut1_eth1_name, sut1_eth2_name, Nic_Type)

        Case.step("run tcpdump")
        sut2.execute_shell_cmd_async('tcpdump -i {} -xx > tcpdump1.log'.format(sut2_eth1_name),
                                     cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)

        Case.step("start testpmd test")
        ret, out, err = sut1.execute_shell_cmd_async(f'python3 dpdk_expect.py start_dpdk_vlan {tool_p}',
                                                     cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.expect('testpmd should be launched and working without errors.', ret == 0)

        Case.step("start scapy test")
        sut2.execute_shell_cmd(f"tar -xzvf {tool}", cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.step('Step 3: send packet ')
        ret, out, err = sut2.execute_shell_cmd(
            f'python3 dpdk_expect.py send_packet_vlan {sut1_mac1_name} {sut1_eth1_name} {scapy_tool_path}', 60 * 5,
            cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.expect('send packet ok', ret == 0)
        ret, out, err = sut1.execute_shell_cmd(
            f'cat {VLAN_LOG}')
        Case.expect('send packet vlan successful !', ret == 0)

        Case.step("download log")
        sut1.download_to_local(remotepath=f'{VLAN_LOG}',
                               localpath=os.path.join(LOG_PATH, 'result'))
        sut2.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/tcpdump1.log',
                               localpath=os.path.join(LOG_PATH, 'result'))

        Case.step("unbind network")
    except Exception as err:
        unbind_dpdk(sut1, sut1_id1, sut1_id2)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_DOWN.format(sut1_eth1_name))[0]
        Case.sleep(5)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_UP.format(sut1_eth1_name))[0]
        Case.sleep(5)
        ret = sut2.execute_shell_cmd(NET_STATE_IFCONFIG_DOWN.format(sut2_eth1_name))[0]
        Case.sleep(5)
        ret = sut2.execute_shell_cmd(NET_STATE_IFCONFIG_UP.format(sut2_eth1_name))[0]
        Case.sleep(5)
        raise err
    finally:
        unbind_dpdk(sut1, sut1_id1, sut1_id2)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_DOWN.format(sut1_eth1_name))[0]
        Case.sleep(5)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_UP.format(sut1_eth1_name))[0]
        Case.sleep(5)
        ret = sut2.execute_shell_cmd(NET_STATE_IFCONFIG_DOWN.format(sut2_eth1_name))[0]
        Case.sleep(5)
        ret = sut2.execute_shell_cmd(NET_STATE_IFCONFIG_UP.format(sut2_eth1_name))[0]
        Case.sleep(5)


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
