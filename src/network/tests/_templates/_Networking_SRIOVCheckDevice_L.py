
from src.network.lib import *
CASE_DESC = [
    'connect sut1 nic port to sut2 nic port cable',
    'create 4 virtual nic on server',
    'set ipv4 and ipv6 address and ping successful'
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

    Case.step("create virtual network")
    nic_id = conn.port1.nic.id_in_os.get(sutos)
    nic_name = valos.get_ether_name(sut1, nic_id, 0)
    ret = sut1.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))
    Case.expect("copy source grub file to /etc/default", ret[0] == 0)
    sut1.execute_shell_cmd('sed -i "s/.*quiet.*/quiet intel_iommu=on/" /etc/default/grub')
    sut1.execute_shell_cmd('grub2-mkconfig -o /etc/default/grub')
    my_os.warm_reset_cycle_step(sut1)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    time.sleep(10)
    retcode = sut1.execute_shell_cmd('echo 4 > /sys/class/net/{}/device/sriov_numvfs'.format(nic_name))[0]
    Case.expect("create 4 sriov", retcode == 0)
    stdout = sut1.execute_shell_cmd("lspci | grep -i 'virtual function' | awk '{print $1}'")[1]
    vf = [i.strip() for i in stdout.splitlines()]
    Case.expect("check sut1 create 4 VF successful", len(vf) == 4)
    time.sleep(10)
    vf_name_1 = sut1.execute_shell_cmd('ls /sys/bus/pci/devices/0000:{}/net'.format(vf[0]))[1]
    vf_name_2 = sut1.execute_shell_cmd('ls /sys/bus/pci/devices/0000:{}/net'.format(vf[1]))[1]

    Case.step("set ipv4 and ping virtual nic")
    ipv4_1 = conn.port1.ip + '0'
    ipv4_2 = conn.port1.ip + '1'
    sut1.execute_shell_cmd("ifconfig {} {}/24 up".format(vf_name_1.strip(), ipv4_1))
    sut1.execute_shell_cmd("ifconfig {} {}/24 up".format(vf_name_2.strip(), ipv4_2))
    time.sleep(10)
    retcode = sut1.execute_shell_cmd("ping -c 5 -I {} {}".format(ipv4_1, ipv4_2))[0]
    Case.expect("sut1 vf port1 ping port2", retcode == 0)
    retcode = sut1.execute_shell_cmd("ping -c 5 -I {} {}".format(ipv4_2, ipv4_1))[0]
    Case.expect("sut1 vf port2 ping port1", retcode == 0)

    Case.step("set ipv6 and ping virtual nic successful")
    valos.ipv6_enable = True
    ipv6_1 = conn.port1.ip + '0'
    ipv6_2 = conn.port1.ip + '1'
    sut1.execute_shell_cmd("ifconfig {} {}/24 up".format(vf_name_1.strip(), ipv6_1))
    sut1.execute_shell_cmd("ifconfig {} {}/24 up".format(vf_name_2.strip(), ipv6_2))
    time.sleep(10)
    retcode = sut1.execute_shell_cmd("ping -c 5 -I {} {}".format(ipv6_1, ipv6_2))[0]
    Case.expect("sut1 ipv6 vf port1 ping port2", retcode == 0)
    retcode = sut1.execute_shell_cmd("ping -c 5 -I {} {}".format(ipv6_2, ipv6_1))[0]
    Case.expect("sut1 ipv6 vf port2 ping port1", retcode == 0)

    Case.step("remove 4 virtual network")
    sut1.execute_shell_cmd('echo 0 > /sys/class/net/"{}"/device/sriov_numvfs'.format(nic_name))
    stdout = sut1.execute_shell_cmd('cat /sys/class/net/{}/device/sriov_numvfs'.format(nic_name))[1]
    Case.expect('delete sut vf', int(stdout.strip()) == 0)

    Case.step("restore grub file")
    sut1.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))


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
