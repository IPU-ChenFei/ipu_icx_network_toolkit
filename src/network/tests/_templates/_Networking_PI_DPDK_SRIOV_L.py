from src.network.lib.dpdk.dpdk_common import *
import xml.etree.cElementTree as elementTree
from src.network.lib import *
CASE_DESC = [
    """
    To check the DPDK functionality in Virtual Function devices by enable IntelVT-d.
    """
]


def get_sriov_xml(vm_name, bus, slot, function):
    """
    Create a pci device xml to attach, return the path of created xml file
    """
    xml_path = f"{project_path}\\src\\network\\lib\\dpdk\\pci_device.xml"

    conf = elementTree.parse(xml_path)
    root = conf.getroot()
    addr = root.find('source/address')
    addr.attrib['bus'] = f'0x{bus}'
    addr.attrib['slot'] = f'0x{slot}'
    addr.attrib['function'] = f'0x{function}'
    xml_tmp = f'{project_path}\\src\\network\\lib\\dpdk\\xml_tmp'
    if not os.path.exists(xml_tmp):
        os.makedirs(xml_tmp)
    vf_file_name = f'pci_device_{vm_name}_{bus}_{slot}_{function}.xml'
    vf_file_path = f'{xml_tmp}\\{vf_file_name}'
    conf.write(vf_file_path)
    return vf_file_path, vf_file_name


def add_vm_vf(sut, vm_name):
    _, nics, _ = sut.execute_shell_cmd('lspci | grep -i Virtual')
    nics = str(nics)[:-1].split('\n')
    en1 = nics[0].strip().split(' ')[0]
    en2 = nics[1].strip().split(' ')[0]
    bus = en1[0:2]
    slot = en1[3:5]
    function = en1[6:]
    vf_xml1_path, vf1_xml_name = get_sriov_xml(vm_name, bus, slot, function)

    bus = en2[0:2]
    slot = en2[3:5]
    function = en2[6:]
    vf_xml2_path, vf2_xml_name = get_sriov_xml(vm_name, bus, slot, function)
    sut.upload_to_remote(localpath=vf_xml1_path,
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    sut.upload_to_remote(localpath=vf_xml2_path,
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    ret = sut.execute_shell_cmd('virsh attach-device {} {} --live --config'
                                .format(vm_name, f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/{vf1_xml_name}'))[0]
    with open(filename, 'a') as name:
    # rhel=vf1.xml
        name.write(f'{vm_name}={bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/{vf1_xml_name}\r')
    Case.expect("add VF successfully", ret == 0)

    ret = sut.execute_shell_cmd('virsh attach-device {} {} --live --config'
                                .format(vm_name, f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/{vf2_xml_name}'))[0]
    with open(filename, 'a') as name:
    # rhel=vf2.xml
        name.write(f'{vm_name}={bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/{vf2_xml_name}\r')
    Case.expect("add VF successfully", ret == 0)

    return vf1_xml_name, vf2_xml_name


def add_dhcp(sut, vm_name):
    ret = sut.execute_shell_cmd('virsh attach-device {} {} --live --config'
                                .format(vm_name, f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/dhcp.xml'))[0]
    Case.expect("add dhcp successfully", ret == 0)
    ret = sut.execute_shell_cmd('virsh domifaddr {}| grep -i 192'.format(vm_name))[1]
    vir_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ret, re.I).group()
    sut.execute_shell_cmd(f'ssh -keygen -R {vir_ip}')
    ret, out, err = sut.execute_shell_cmd(f'python3 vm_dpdk.py scp_file {vir_ip} {VM_DPDK_PATH}', 60 * 5,
                                          cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    Case.expect('scp file successfully', ret == 0)
    ret, out, err = sut.execute_shell_cmd(f'python3 vm_dpdk.py rm_old_yum {vir_ip} ', 60 * 5,
                                          cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    ret, out, err = sut.execute_shell_cmd(f'python3 vm_dpdk.py scp_file {vir_ip} {sut_yum_repo} {yum_repo}', 60 * 5,
                                          cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    Case.expect('scp repo file successfully', ret == 0)
    Case.sleep(10)
    return vir_ip


def set_grub(sut, tool_path, my_os):
    ret = sut.execute_shell_cmd('cp -f {}/grub /etc/default'.format(tool_path))
    Case.expect("copy source grub file to sut /etc/default", ret[0] == 0)
    sut.execute_shell_cmd('sed -i "s/quiet/quiet intel_iommu=on iommu=pt/" /etc/default/grub')
    sut.execute_shell_cmd('grub2-mkconfig -o /etc/default/grub', timeout=600)
    my_os.warm_reset_cycle_step(sut)


def echo_vf(sut, nic_type):
    _, nics, _ = sut.execute_shell_cmd('lspci | grep -i {}'.format(nic_type))
    nics = str(nics)[:-1].split('\n')
    sut_id1 = nics[0].strip().split(' ')[0]
    sut_id2 = nics[1].strip().split(' ')[0]
    ret = sut.execute_shell_cmd('echo 1 > /sys/bus/pci/devices/0000:{}/sriov_numvfs'.format(sut_id1))[0]
    Case.expect('echo network successfully', ret == 0)
    ret = sut.execute_shell_cmd('echo 1 > /sys/bus/pci/devices/0000:{}/sriov_numvfs'.format(sut_id2))[0]
    Case.expect('echo network successfully', ret == 0)


def vm_install(sut, vm_name):
    ret = sut.execute_shell_cmd(COPY_IMAGE.format(vm_name))[0]
    Case.expect("copy vm successfully", ret == 0)
    ret = sut.execute_shell_cmd(f'virt-install --name {vm_name} --ram 6000 --vcpus 10 --disk '
                                f'/var/lib/libvirt/images/{vm_name}.qcow2,bus=virtio --import --noautoconsole --os-variant '
                                'rhel7.0')[0]
    Case.sleep(60)
    Case.expect("install vm successfully", ret == 0)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    vm_name = 'dpdk_rhel_{}'.format(int(time.time()))
    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    portname = ParameterParser.parse_parameter("portname")
    portname = 'enp0s20f0u1'
    add_dhcp_xml(portname)
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)
    Nic_Type = conn.port1.nic.id_in_os[sutos]

    Case.prepare("prepare steps and upload python file")
    boot_to(sut, sut.default_os)

    Case.step("upload py file")
    upload_dpdk_file(sut)

    Case.step("set SRIOV enable in BIOS")
    #sut.set_bios_knobs(*bios_knob('enable_sriov_xmlcli'))
    set_bios_knobs_step(sut, *bios_knob('enable_sriov_xmlcli'), *bios_knob('enable_vtd_xmlcli'))
    #sut.set_bios_knobs_xmlcli('SRIOVEnable=0x1', sut.default_os)
    #sut.set_bios_knobs(*bios_knob('enable_vtd_xmlcli'))
    #sut.set_bios_knobs_xmlcli('VTdSupport=0x1', sut.default_os)

    Case.step("echo intel_iommu=on iommu=pt in sut")
    set_grub(sut, valos.tool_path, my_os)
    Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)

    Case.step("set up virtual")
    echo_vf(sut, Nic_Type)

    Case.step("vm install")
    vm_install(sut, vm_name)

    Case.step("create xml file and add VF")
    add_vm_vf(sut, vm_name)

    Case.step("add vm dhcp and scp dpdk,repo file")
    vir_ip = add_dhcp(sut, vm_name)
    ret = sut.execute_shell_cmd('virsh reboot {}'.format(vm_name))[0]
    Case.expect("vm reboot successfully", ret == 0)
    Case.sleep(60)

    Case.step("install dpdk in vm")
    ret, out, err = sut.execute_shell_cmd(f'python3 vm_dpdk.py install_dpdk {vir_ip}', 60 * 100,
                                          cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    Case.expect('install vm dpdk successfully', ret == 0)
    """
    ip = args[0]
    path = args[1]
    path2 = args[2]
    en1 = args[3]
    en2 = args[4]
    """

    Case.step("start testpmd tx_first in vm")
    ret, out, err = sut.execute_shell_cmd(f'python3 vm_dpdk.py start_dpdk_vm {vir_ip}', 60 * 60,
                                          cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    Case.expect('start vm tx_first successfully', ret == 0)

    Case.step("download log file")
    sut.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/install_1.log',
                          localpath=os.path.join(LOG_PATH, 'result'))
    sut.download_to_local(remotepath=f'{bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK}/start_dpdk.log',
                          localpath=os.path.join(LOG_PATH, 'result'))


def clean_up(sut):
    from dtaf_core.lib.tklib.steps_lib import cleanup
    if Result.returncode != 0:
        clear_settings(sut, filename)
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
