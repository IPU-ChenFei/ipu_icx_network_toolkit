from auto_api import *
from infra.sut import get_sut_list, get_default_sut
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step
from src.lib.toolkit.steps_lib.config import bios_knob
from src.lib.toolkit.steps_lib.domains.network.network import val_os
from src.lib.toolkit.steps_lib.domains.network.config import nic_config
from src.network.lib.vm.vm_host import vm_setup
from src.lib.toolkit.steps_lib.os_scene import *
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'set ipv4 for Mellanox nic',
    'running iwvss stress test'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    # pkg = ParameterParser.parse_parameter("tool")
    # conf = ParameterParser.parse_parameter("conf")
    # flow = ParameterParser.parse_parameter("flow")
    valos = val_os(sutos)

    # step 1: get sut instance
    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    # step 2: prepare steps
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    sut1.upload_to_remote(os.path.join(valos.common_path, "vm", "vm_sut_ixvss_l.py"), valos.tool_path)

    # step 3: set SRIOV enable in BIOS
    set_bios_knobs_step(sut1, *bios_knob('enable_sriov_xmlcli'))
    set_bios_knobs_step(sut1, *bios_knob('enable_vtd_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('enable_sriov_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('enable_vtd_xmlcli'))

    # step 4: echo intel_iommu=on iommu=pt in sut1
    sut1_nic_id = conn.port1.nic.id_in_os.get(sutos)
    ret = sut1.execute_shell_cmd('cp -f {}/grub /etc/default'.format(valos.tool_path))
    Case.expect("copy source grub file to sut1 /etc/default", ret[0] == 0)
    sut1.execute_shell_cmd('sed -i "s/quiet/quiet intel_iommu=on iommu=pt/" /etc/default/grub')
    sut1.execute_shell_cmd('grub2-mkconfig -o /etc/default/grub', timeout=600)
    my_os.warm_reset_cycle_step(sut1)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    # step 6: set IB
    valos.switch_infiniband_mode(sut1, "IB", "rhel")
    valos.switch_infiniband_mode(sut2, "IB", "rhel")
    valos.ip_assign(conn)
    sut1_nic_name = valos.get_ether_name(sut1, sut1_nic_id, 0)

    # step 7: config opensm.conf
    ret = sut1.execute_shell_cmd('echo virt_enabled 2 > /etc/opensm/opensm.conf')
    Case.expect("config opensm.conf", ret[0] == 0)

    # step 8: Enable SR-IOV on the Firmware in sut1
    _, stdout, _ = sut1.execute_shell_cmd("mst status |grep -i mt | awk -F ' ' '{print $1}'")
    sut1.execute_shell_cmd("mlxconfig -y -d {} query".format(stdout.strip()))
    sut1.execute_shell_cmd("mlxconfig -y -d {} set SRIOV_EN=1 NUM_OF_VFS=4".format(stdout.strip()))
    sut1.execute_shell_cmd("mlxfwreset -y --device {} reset".format(stdout.strip()))

    # step 9: Enable SR-IOV on the MLNX_OFED driver in sut1
    sut1.execute_shell_cmd("echo 4 > /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")
    stdout = sut1.execute_shell_cmd("cat /sys/class/infiniband/mlx5_0/device/mlx5_num_vfs")[1]
    Case.expect('there is 4 vf', int(stdout.strip()) == 4)

    # step 10: create the port GUID and node GUIDs configuration is as expected in sut1
    stdout = sut1.execute_shell_cmd("lspci | grep -i 'virtual function' | awk '{print $1}'")[1]
    sut1_vf = [i.strip() for i in stdout.splitlines()]
    Case.expect("create 4 sut1_vf", len(sut1_vf) == 4)
    sut1.execute_shell_cmd('echo 0000:{} > /sys/bus/pci/drivers/mlx5_core/unbind'.format(sut1_vf[-1]))
    stdout = sut1.execute_shell_cmd('ls /sys/class/infiniband/mlx5_0/device/sriov/')[1]
    sut1_vf_num = stdout.split()[-1]
    sut1.execute_shell_cmd(
        'echo 11:22:33:44:77:66:77:90 > /sys/class/infiniband/mlx5_0/device/sriov/{}/node'.format(sut1_vf_num))
    sut1.execute_shell_cmd(
        'echo 11:22:33:44:77:66:77:91 > /sys/class/infiniband/mlx5_0/device/sriov/{}/port'.format(sut1_vf_num))
    stdout = sut1.execute_shell_cmd(
        'cat /sys/class/infiniband/mlx5_0/device/sriov/{}/node | grep -i "11:22:33:44:77:66:77:90"'.format(sut1_vf_num))
    Case.expect('echo node is pass', stdout)
    sut1.execute_shell_cmd(
        'cat /sys/class/infiniband/mlx5_0/device/sriov/{}/port  | grep -i "11:22:33:44:77:66:77:91"'.format(
            sut1_vf_num))
    Case.expect('echo port is pass', stdout)
    sut1.execute_shell_cmd('echo 0000:{} > /sys/bus/pci/drivers/mlx5_core/bind'.format(sut1_vf[-1]))
    sut1.execute_shell_cmd('echo Follow > /sys/class/infiniband/mlx5_0/device/sriov/{}/policy'.format(sut1_vf_num))
    stdout = sut1.execute_shell_cmd(
        'cat /sys/class/infiniband/mlx5_0/device/sriov/{}/policy | grep -i "Follow"'.format(sut1_vf_num))
    Case.expect('policy is Follow', stdout)
    ret = sut1.execute_shell_cmd('mst restart & systemctl restart opensm')
    Case.expect("restart opensm", ret[0] == 0)
    retcode = sut1.execute_shell_cmd('ibdev2netdev -v | grep -i "{}" | grep -i "up"'.format(sut1_vf[-1]))[0]
    Case.expect("sut1_vf up", retcode == 0)

    # step 11: verify that the port GUID and node GUIDs configuration is as expected
    _, stdout, _ = sut1.execute_shell_cmd('ibstat | grep -i "1122334477667790"')
    Case.expect('wait result test pass', stdout)
    _, stdout, _ = sut1.execute_shell_cmd('ibstat | grep -i "1122334477667791"')
    Case.expect('wait result test pass', stdout)

    # step 12: Set up Vm
    vm_setup(sut1, "fio")

    # step 13: Running fio
    ret, sut1_vm_ip, err = sut1.execute_shell_cmd("cd /home/BKCPkg/domains/network/ && python vm_sut_fio_l.py "
                                                  f"--net_inter={sut1_nic_name} "
                                                  "--vm_name=RH_VM ", timeout=180)
    if ret != 0:
        raise RuntimeError(err)

    sut2.execute_shell_cmd("mkdir -p /home/nfstemp & touch /home/nfstemp/target")
    sut2.execute_shell_cmd(f'echo "/home/nfstemp {sut1_vm_ip}(rw,sync,no_root_squash)" > /etc/exports')
    sut2.execute_shell_cmd('systemctl restart nfs-server')
    ret, stdout, stderr = sut2.execute_shell_cmd('showmount -e')
    Case.expect('nfs service is open', f'/home/nfstemp {sut1_vm_ip}' in stdout)

    ret, stdout, err = sut1.execute_shell_cmd("cd /home/BKCPkg/domains/network/ && python vm_sut_fio_l.py "
                                              "--vm_name=RH_VM "
                                              f"--net_inter={sut1_nic_name} "
                                              f"--sut2_ip={conn.port2.ip}", timeout=3000)
    Case.expect('run fio command successfully', ret == 0)
    Case.expect('fio stress test without error', 'testnfs: (groupid=0, jobs=1): err= 0' in stdout)

    # step 14: restore env
    sut2.execute_shell_cmd('systemctl stop nfs-server')
    sut2.execute_shell_cmd('rm -f -r /home/nfstemp')

    set_bios_knobs_step(sut1, *bios_knob('disable_sriov_xmlcli'))
    set_bios_knobs_step(sut1, *bios_knob('disable_vtd_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('disable_sriov_xmlcli'))
    set_bios_knobs_step(sut2, *bios_knob('disable_vtd_xmlcli'))


def clean_up(sut):
    from src.lib.toolkit.steps_lib import cleanup
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

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)