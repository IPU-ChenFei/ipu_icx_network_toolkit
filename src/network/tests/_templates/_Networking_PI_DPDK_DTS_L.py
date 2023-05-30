
from src.network.lib.dpdk.dpdk_common import *
#from src.configuration.config.sut_tool import bhs_sut_tools
from src.network.lib import *
CASE_DESC = [
    """
    This test case is to validate those key DPDK test sutie cases (L2fwd/L3fwd/RX TX callbacks)
    """
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
    Nic_Type = conn.port1.nic.id_in_os[sutos]
    try:
        Case.step("set ipv4")
        valos.ip_assign(conn)

        Case.step("upload dpdk python file")
        upload_dpdk_file(sut1)

        Case.step("set dpdk environment")
        set_dpdk(sut1)
        sut1_eth1_name = valos.get_ether_name(sut1, Nic_Type, 0)
        sut1_eth2_name = valos.get_ether_name(sut1, Nic_Type, 1)
        sut_id1, sut_id2 = bind_dpdk(sut1, sut1_eth1_name, sut1_eth2_name, Nic_Type)

        Case.step("run L2fwd test")
        ret, res, err = sut1.execute_shell_cmd('python3 dpdk_expect.py start_dpdk_L2fwd {}'.format(tool1_p), 60 * 5,
                                              cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.expect("L2fwd test run successfully", "error" in res or ret == 0)

        Case.step("run L3fwd test")
        ret, res, err = sut1.execute_shell_cmd(f'python3 dpdk_expect.py start_dpdk_L3fwd {tool1_p}', 60 * 5,
                                              cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.expect("L3fwd test run successfully", "error" in res or ret == 0)

        Case.step("run RX/TX Callbacks(cpu reach 100)")
        ret, res, err = sut1.execute_shell_cmd_async(f'python3 dpdk_expect.py start_dpdk_RXTX {tool1_p}', 60 * 5,
                                                    cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
        Case.sleep(10)
        ret = sut1.execute_shell_cmd_async('export TERM=dumb && top > RXTX_top.log', cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
        Case.expect("RXTX test run successfully", "error" in res or ret == 0)
        Case.sleep(10)

        Case.step("download stress log")
        sut1.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/L2.log',
                              localpath=os.path.join(LOG_PATH, 'result'))
        sut1.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/L3.log',
                              localpath=os.path.join(LOG_PATH, 'result'))
        sut1.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/RXTX.log',
                              localpath=os.path.join(LOG_PATH, 'result'))
        sut1.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/RXTX_top.log',
                              localpath=os.path.join(LOG_PATH, 'result'))
    except Exception as err:
        Case.step("unbind network")
        unbind_dpdk(sut1, sut_id1, sut_id2)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_DOWN.format(sut1_eth1_name))[0]
        Case.sleep(5)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_UP.format(sut1_eth1_name))[0]
        Case.sleep(5)
        raise err
    finally:
        Case.step("unbind network")
        unbind_dpdk(sut1, sut_id1, sut_id2)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_DOWN.format(sut1_eth1_name))[0]
        Case.sleep(5)
        ret = sut1.execute_shell_cmd(NET_STATE_IFCONFIG_UP.format(sut1_eth1_name))[0]
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
