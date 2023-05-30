
from src.network.lib.dpdk.dpdk_common import *
#from src.configuration.config.sut_tool import bhs_sut_tools
from src.network.lib import *
CASE_DESC = [
    'This case is to run packet forwarding test with DPDK mode and the pktgen test.'
]


def prepare_pktgen(sut2, tool):
    ret = sut2.execute_shell_cmd("tar -xzvf {}".format(tool), cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
    Case.expect("tar sut2 pktgen tool successfully", ret == 0)
    ret = sut2.execute_shell_cmd(r"yum install libpcap*")[0]
    Case.expect('yum install pass', ret == 0)
    ret = sut2.execute_shell_cmd('export PKG_CONFIG_PATH=/usr/local/lib64/pkgconfig && make',
                                 cwd=bhs_sut_tools.NW_PKTGEN_ISTALL_L)[0]
    Case.expect("make successfully", ret == 0)
    ret = sut2.execute_shell_cmd('ldconfig', cwd=bhs_sut_tools.NW_PKTGEN_ISTALL_L)[0]
    Case.expect("ldconfig successfully", ret == 0)

class Dpdk(object):
    @classmethod
    def _remove_special_and_specific_character(cls, string, specialword):
        """
        remove special and specific characters form str

        Args:
            string: the string that need to be modified
            specialword: Special character to be deleted

        Returns:
            changestr: modified string
        """
        changestr = string
        changestr = changestr.replace(specialword, ' ')
        changestr = changestr.replace('<UP-', ' ')
        changestr = changestr.replace('-FD>', ' ')
        changestr = changestr.replace('', ' ')
        changestr = changestr.replace('[K', ' ')
        changestr = changestr.replace(',', ' ')
        changestr = changestr.replace(' ', '')
        return changestr

    @classmethod
    def _result_check(cls, testvalue, targetvalue):
        """
        Check the result to determine whether the result meets the expected value

        Args:
            testvalue: test value
            targetvalue: The target value is plus or minus 50% of the target value

        Returns:
            result: If the result is False, the test failed, and if the result is True, the test is successful
        """
        result = False
        if (testvalue >= targetvalue * 0.5) and (testvalue <= targetvalue * 1.5):
            result = True
        return result

    @classmethod
    def _get_port_speed(cls, path, keywordstart, keywordend):
        """
        Get the port speed of network card form the result file

        Args:
            path: result file path
            keywordstart: The start position of the keyword in the file for the network port speed
            keywordend: The end position of the keyword in the file for the network port speed

        Returns:
            speed:  network card speed
        """
        file = open(path)
        abnormalvalue = "<--Down-->"
        speed = 0
        for str in file.readlines():
            if (keywordstart in str) and (keywordend in str):
                str = str[str.rfind(keywordstart):str.rfind(keywordend)]
                if abnormalvalue not in str:
                    speed = int(cls._remove_special_and_specific_character(str, keywordstart))
                    break
        file.close()
        return speed

    @classmethod
    def _get_mbits_tx_result(cls, path, keywordstart, keywordend):
        """
        Get the Mbits/s Tx form the result file

        Args:
            path: result file path
            keywordstart: The start position of the keyword in the file
            keywordend: The end position of the keyword in the file

        Returns:
            Tx:  Mbits/s Tx
        """
        file = open(path)
        abnormalvalue = "0/0"
        Tx = 0
        for str in file.readlines():
            if (keywordstart in str) and (keywordend in str):
                findcount = str.count(keywordstart)
                count =0
                for count in range(0, findcount):
                    count = count + 1
                    str1 = str[str.find(keywordstart):str.find(keywordend)]
                    if abnormalvalue not in str1:
                        str1 = cls._remove_special_and_specific_character(str1, keywordstart)
                        Tx = int(str1[str1.rfind("/") + 1:])
                    else:
                        str = str[str.find(keywordend)+1:len(str)]
                        continue
        file.close()
        return Tx

    @classmethod
    def pkt_log_result_deal(cls, path):
        """
        PKT log result deal

        Args:
            path: result file path

        Returns:
            result: If the result is False, the test failed, and if the result is True, the test is successful
        """
        # Step1: get Mbits Tx result
        result = False
        port0_start = "[6;22H"
        port0_end = "[7;22H"
        port1_start = "[6;43H"
        port1_end = "[7;43H"

        P0Tx = cls._get_mbits_tx_result(path, port0_start, port0_end)
        P1Tx = cls._get_mbits_tx_result(path, port1_start, port1_end)

        # Step2: get port speed
        port0_speed_start = "[3;22H"
        port0_speed_end = "[4;22H"
        port1_speed_start = "[3;43H"
        port1_speed_end = "[4;43H"

        P0Speed = cls._get_port_speed(path, port0_speed_start, port0_speed_end)
        P1Speed = cls._get_port_speed(path, port1_speed_start, port1_speed_end)

        # Step3: result check
        P0result = cls._result_check(P0Tx, P0Speed)
        P1result = cls._result_check(P1Tx, P1Speed)

        if (P0result == True) and (P1result == True):
            result = True
        return result


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

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    try:
        Case.step("set ipv4")
        valos.ip_assign(conn)

        Case.step("upload the python file")
        upload_dpdk_file(sut1)
        upload_dpdk_file(sut2)

        Case.step("get nic info")
        sut1_mac1_name = valos.get_mac_address(sut1, conn.port1.nic.id_in_os.get(sutos), 0)
        sut1_mac2_name = valos.get_mac_address(sut1, conn.port1.nic.id_in_os.get(sutos), 1)
        sut1_eth1_name = valos.get_ether_name(sut1, conn.port1.nic.id_in_os.get(sutos), 0)
        sut1_eth2_name = valos.get_ether_name(sut1, conn.port1.nic.id_in_os.get(sutos), 1)
        sut2_eth1_name = valos.get_ether_name(sut2, conn.port2.nic.id_in_os.get(sutos), 0)
        sut2_eth2_name = valos.get_ether_name(sut2, conn.port2.nic.id_in_os.get(sutos), 1)

        Case.step("set dpdk environment")
        set_dpdk(sut1, number_huge=4096)
        set_dpdk(sut2, number_huge=4096)

        Case.step("bind 2 suts 2 ports to vfio")
        sut1_id1, sut1_id2 = bind_dpdk(sut1, sut1_eth1_name, sut1_eth2_name, Nic_Type)
        sut2_id1, sut2_id2 = bind_dpdk(sut2, sut2_eth1_name, sut2_eth2_name, Nic_Type)

        Case.step("sut2 prepare pktgen")
        prepare_pktgen(sut2, tool)

        Case.step("start pmd and pkgten test,run time 12h")
        tool_path = f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/build/app'
        ret, out, err = sut1.execute_shell_cmd_async(f'python3 dpdk_expect.py '
                                                     f'tart_dpdk_pmd1 {tool_path}', 60 * 60 * 20,
                                                     cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.expect('testpmd should be launched and working without errors.', ret == 0)
        ret, out, err = sut2.execute_shell_cmd_async(
            f'python3 dpdk_expect.py start_dpdk_pktgen {sut1_mac1_name} {sut1_mac2_name} {pktgen_tool_path}', 60 * 60 * 20,
            cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.expect('start pktgen stress successfully', ret == 0)
        Case.sleep(60)
        #ret = sut2.execute_shell_cmd(r"sed 's/\x1b//g' PKT.log > PKT2.log", cwd=sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
        #Case.expect("sed successfully", ret == 0)

        Case.step("download the log")
        sut2.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/PKT.log',
                               localpath=os.path.join(LOG_PATH, 'result'))

        Case.step("unbind the network")

        sut2.execute_shell_cmd(
            f'DISPLAY=:0 gnome-terminal --window --full-screen -- bash -c "cat {bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/PKT.log;exec bash"')
        Case.sleep(10)
        Case.snapshot('dpdk_stress')

        pktlogpath = os.path.join(LOG_PATH, 'result\\PKT.log')
        dpdk = Dpdk()
        ret = dpdk.pkt_log_result_deal(pktlogpath)
        Case.expect("PKT.log check successfully", ret == True)
    except Exception as err:
        unbind_dpdk(sut1, sut1_id1, sut1_id2)
        unbind_dpdk(sut2, sut2_id1, sut2_id2)
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
        unbind_dpdk(sut2, sut2_id1, sut2_id2)
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
