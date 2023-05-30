
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'Validate the SR-IOV capability of the Infiniband adapter'
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

    Case.step("set SRIOV enable in BIOS")
    set_bios_knobs_step(sut1, *bios_knob('enable_sriov_xmlcli'), *bios_knob('enable_vtd_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('enable_sriov_xmlcli'), *bios_knob('enable_vtd_xmlcli'))

    Case.step("echo intel_iommu=on iommu=pt in sut1")
    ret = sut1.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))
    Case.expect("copy source grub file to sut1 /etc/default", ret[0] == 0)
    sut1.execute_shell_cmd('sed -i "s/quiet/quiet intel_iommu=on iommu=pt/" /etc/default/grub')
    sut1.execute_shell_cmd('grub2-mkconfig -o /etc/default/grub', timeout=600)
    my_os.warm_reset_cycle_step(sut1)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("echo intel_iommu=on iommu=pt in sut2")
    ret = sut2.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))
    Case.expect("copy source grub file to sut2 /etc/default", ret[0] == 0)
    sut2.execute_shell_cmd('sed -i "s/quiet/quiet intel_iommu=on iommu=pt/" /etc/default/grub')
    sut2.execute_shell_cmd('grub2-mkconfig -o /etc/default/grub', timeout=600)
    sut2.execute_shell_cmd('shutdown -r now')
    Case.sleep(60)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    Case.wait_and_expect('wait for restoring sut1 ssh connection', 60 * 5, sut1.check_system_in_os)

    Case.step("set IB & set ip")
    valos.switch_infiniband_mode(sut1, "IB")
    valos.switch_infiniband_mode(sut2, "IB")
    valos.ip_assign(conn)

    Case.step("config opensm.conf")
    sut1.execute_shell_cmd('echo virt_enabled 2 > /etc/opensm/opensm.conf')
    sut2.execute_shell_cmd('echo virt_enabled 2 > /etc/opensm/opensm.conf')

    Case.step("Enable SR-IOV on the Firmware in sut1")
    _, stdout, _ = sut1.execute_shell_cmd("mst status |grep -i mt | awk -F ' ' '{print $1}'")
    sut1.execute_shell_cmd("mlxconfig -y -d {} query".format(stdout.strip()))
    sut1.execute_shell_cmd("mlxconfig -y -d {} set SRIOV_EN=1 NUM_OF_VFS=4".format(stdout.strip()))
    sut1.execute_shell_cmd("mlxfwreset -y --device {} reset".format(stdout.strip()))

    Case.step("Enable SR-IOV on the Firmware in sut2")
    _, stdout, _ = sut2.execute_shell_cmd("mst status |grep -i mt | awk -F ' ' '{print $1}'")
    sut2.execute_shell_cmd("mlxconfig -y -d {} query".format(stdout.strip()))
    sut2.execute_shell_cmd("mlxconfig -y -d {} set SRIOV_EN=1 NUM_OF_VFS=4".format(stdout.strip()))
    sut2.execute_shell_cmd("mlxfwreset -y --device {} reset".format(stdout.strip()))

    Case.step("Enable SR-IOV on the MLNX_OFED driver in sut1")
    stdout = sut1.execute_shell_cmd("cat /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")[1]
    Case.expect('there is no vf', int(stdout.strip()) == 0)
    sut1.execute_shell_cmd("echo 4 > /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")
    stdout = sut1.execute_shell_cmd("cat /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")[1]
    Case.expect('there is 4 vf', int(stdout.strip()) == 4)

    Case.step("Enable SR-IOV on the MLNX_OFED driver in sut2")
    stdout = sut2.execute_shell_cmd("cat /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")[1]
    Case.expect('there is no vf', int(stdout.strip()) == 0)
    sut2.execute_shell_cmd("echo 4 > /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")
    stdout = sut2.execute_shell_cmd("cat /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")[1]
    Case.expect('there is 4 vf', int(stdout.strip()) == 4)

    Case.step("create the port GUID and node GUIDs configuration is as expected in sut1")
    stdout = sut1.execute_shell_cmd("lspci | grep -i 'virtual function' | awk '{print $1}'")[1]
    sut1_vf = [i.strip() for i in stdout.splitlines()]
    Case.expect("create 4 sut1_vf", len(sut1_vf) == 4)
    retcode = sut1.execute_shell_cmd('echo 0000:{} > /sys/bus/pci/drivers/mlx5_core/unbind'.format(sut1_vf[-1]))[0]
    Case.expect('execute echo cmd', retcode == 0)
    stdout = sut1.execute_shell_cmd('ls /sys/class/infiniband/mlx5_0/device/sriov/')[1]
    sut1_vf_num = stdout.split()[-1]
    sut1.execute_shell_cmd('echo 11:22:33:44:77:66:77:90 > /sys/class/infiniband/mlx5_0/device/sriov/{}/node'.format(sut1_vf_num))
    sut1.execute_shell_cmd('echo 11:22:33:44:77:66:77:91 > /sys/class/infiniband/mlx5_0/device/sriov/{}/port'.format(sut1_vf_num))
    stdout = sut1.execute_shell_cmd('cat /sys/class/infiniband/mlx5_0/device/sriov/{}/node | grep -i "11:22:33:44:77:66:77:90"'.format(sut1_vf_num))
    Case.expect('echo node is pass', stdout)
    sut1.execute_shell_cmd('cat /sys/class/infiniband/mlx5_0/device/sriov/{}/port  | grep -i "11:22:33:44:77:66:77:91"'.format(sut1_vf_num))
    Case.expect('echo port is pass', stdout)
    sut1.execute_shell_cmd('echo 0000:{} > /sys/bus/pci/drivers/mlx5_core/bind'.format(sut1_vf[-1]))
    sut1.execute_shell_cmd('echo Follow > /sys/class/infiniband/mlx5_0/device/sriov/{}/policy'.format(sut1_vf_num))
    stdout = sut1.execute_shell_cmd('cat /sys/class/infiniband/mlx5_0/device/sriov/{}/policy | grep -i "Follow"'.format(sut1_vf_num))
    Case.expect('policy is Follow', stdout)
    stdout = sut1.execute_shell_cmd('mst restart & systemctl restart opensm')
    retcode = sut1.execute_shell_cmd('ibdev2netdev -v | grep -i "{}" | grep -i "up"'.format(sut1_vf[-1]))[0]
    Case.expect("sut1_vf up", retcode == 0)

    Case.step("create the port GUID and node GUIDs configuration is as expected in sut2")
    stdout = sut2.execute_shell_cmd("lspci | grep -i 'virtual function' | awk '{print $1}'")[1]
    sut2_vf = [i.strip() for i in stdout.splitlines()]
    Case.expect("create 4 sut2_vf", len(sut2_vf) == 4)
    sut2.execute_shell_cmd('echo 0000:{} > /sys/bus/pci/drivers/mlx5_core/unbind'.format(sut2_vf[-1]))
    stdout = sut2.execute_shell_cmd('ls /sys/class/infiniband/mlx5_0/device/sriov/')[1]
    sut2_vf_num = stdout.split()[-1]
    sut2.execute_shell_cmd('echo 11:22:33:44:77:66:77:60 > /sys/class/infiniband/mlx5_0/device/sriov/{}/node'.format(sut2_vf_num))
    sut2.execute_shell_cmd('echo 11:22:33:44:77:66:77:61 > /sys/class/infiniband/mlx5_0/device/sriov/{}/port'.format(sut2_vf_num))
    stdout = sut2.execute_shell_cmd('cat /sys/class/infiniband/mlx5_0/device/sriov/{}/node | grep -i "11:22:33:44:77:66:77:90"'.format(sut2_vf_num))
    Case.expect('echo node is pass', stdout)
    sut2.execute_shell_cmd('cat /sys/class/infiniband/mlx5_0/device/sriov/{}/port  | grep -i "11:22:33:44:77:66:77:91"'.format(sut2_vf_num))
    Case.expect('echo port is pass', stdout)
    sut2.execute_shell_cmd('echo 0000:{} > /sys/bus/pci/drivers/mlx5_core/bind'.format(sut2_vf[-1]))
    sut2.execute_shell_cmd('echo Follow > /sys/class/infiniband/mlx5_0/device/sriov/{}/policy'.format(sut2_vf_num))
    stdout = sut2.execute_shell_cmd('cat /sys/class/infiniband/mlx5_0/device/sriov/{}/policy | grep -i "Follow"'.format(sut2_vf_num))
    Case.expect('policy is Follow', stdout)
    stdout = sut2.execute_shell_cmd('mst restart & systemctl restart opensm')
    retcode = sut2.execute_shell_cmd('ibdev2netdev -v | grep -i "{}" | grep -i "up"'.format(sut2_vf[-1]))[0]
    Case.expect("sut2_vf up", retcode == 0)

    Case.step("verify that the port GUID and node GUIDs configuration is as expected")
    _, stdout, _ = sut1.execute_shell_cmd('ibstat | grep -i "1122334477667790"')
    Case.expect('wait result test pass', stdout)
    _, stdout, _ = sut1.execute_shell_cmd('ibstat | grep -i "1122334477667791"')
    Case.expect('wait result test pass', stdout)
    _, stdout, _ = sut2.execute_shell_cmd('ibstat | grep -i "1122334477667760"')
    Case.expect('wait result test pass', stdout)
    _, stdout, _ = sut2.execute_shell_cmd('ibstat | grep -i "1122334477667761"')
    Case.expect('wait result test pass', stdout)

    Case.step("Set up Vm")
    vm_setup(sut1)
    vm_setup(sut2)

    sut1_nic_id = conn.port1.nic.id_in_os.get(sutos)
    sut1_nic_name = valos.get_ether_name(sut1, sut1_nic_id, 0)
    sut2_nic_id = conn.port2.nic.id_in_os.get(sutos)
    sut2_nic_name = valos.get_ether_name(sut2, sut2_nic_id, 0)

    ret, out, err = sut2.execute_shell_cmd("cd /home/BKCPkg/domains/network/ && python vm_sut_l.py "
                                           "--sut_no=sut2 "
                                           "--vm_name=RH_VM "
                                           f"--net_inter={sut2_nic_name}", timeout=180)
    if ret != 0:
        raise RuntimeError(err)
    ret, _, err = sut1.execute_shell_cmd("cd /home/BKCPkg/domains/network/ && python vm_sut_l.py "
                                         "--sut_no=sut1 "
                                         "--vm_name=RH_VM "
                                         "--net_inter={}".format(sut1_nic_name), timeout=180)
    if ret != 0:
        raise RuntimeError(err)
    ret, _, err = sut2.execute_shell_cmd("cd /home/BKCPkg/domains/network/ && python vm_sut_l.py "
                                         "--sut_no=sut2 "
                                         "--vm_name=RH_VM "
                                         f"--net_inter={sut2_nic_name} "
                                         "-d", timeout=180)
    if ret != 0:
        raise RuntimeError(err)
    ret, _, err = sut1.execute_shell_cmd("cd /home/BKCPkg/domains/network/ && python vm_sut_l.py "
                                         "--sut_no=sut1 "
                                         "--vm_name=RH_VM "
                                         f"--net_inter={sut1_nic_name} "
                                         "-d", timeout=180)
    if ret != 0:
        raise RuntimeError(err)

    Case.step("restore SUT1 and SUT2 network interface back to ETH mode and grub file")
    valos.switch_infiniband_mode(sut1, "ETH")
    valos.switch_infiniband_mode(sut2, "ETH")
    sut1.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))
    sut2.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))


def clean_up(sut, sut2):
    #set_bios_knobs_step(sut, *bios_knob('disable_sriov_xmlcli'))
    #set_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
    #set_bios_knobs_step(sut2, *bios_knob('disable_sriov_xmlcli'))
    #set_bios_knobs_step(sut2, *bios_knob('disable_vtd_xmlcli'))

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
    sut2 = get_sut_list()[1]
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)
    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut, sut2)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
