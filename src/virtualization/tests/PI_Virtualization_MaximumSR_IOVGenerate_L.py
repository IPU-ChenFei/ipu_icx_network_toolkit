"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883512
 @Author:
 @Prerequisite:
    1. HW Configuration
        1. A X710 network card plug in PCIe, connect to external network with port 0 and port 1
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
            1. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
    3. Virtual Machine
        1. A Linux virtual machine named "rhel1"
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'This section ensures that correct number of VFs are present in the host OS after configuring the OS to support '
    'SRIOV and the driver for VF can be installed The test case depend on the PCIE-device, set to manual in PSS '
    'Stage, update test content to latest hardware (NIC) in silicon stage '
]


def static_ip_assgin(kvm, vm_name, target_v_nic):
    bus, slot, func = split_pci_dev_id(target_v_nic)
    kvm.start_vm(vm_name)
    kvm.attach_nic_to_vm(vm_name, bus, slot, func)
    rcode, std_out, std_err = kvm.execute_vm_cmd(vm_name, "lspci |grep -i 'Virtual Function'")
    nics = str(std_out)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')
    kvm.execute_vm_cmd(vm_name, f'dhclient -r && dhclient')


def dhcp_ip_assgin(kvm, vm_name):
    rcode, std_out, std_err = kvm.execute_vm_cmd(vm_name, "lspci |grep -i 'Virtual Function'")
    nics = str(std_out)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')
    bdf = target_nic[0].strip()
    out = ""
    kvm.execute_vm_cmd(vm_name, f'dhclient -r && dhclient')

    _, ether_name, std_err = kvm.execute_vm_cmd(vm_name, f'ls /sys/bus/pci/devices/0000:{bdf}/net')
    for i in range(10):
        # _, out, std_err = kvm.execute_vm_cmd(vm_name, f"ifconfig {ether_name} | sed -n '2,1p' | awk '{{print $2}}'")
        _, out, std_err = kvm.execute_vm_cmd(vm_name, f"ifconfig {ether_name}")
        if len(log_check.find_lines("inet", out)) != 0:
            out = log_check.scan_format("inet %s", out)[0]
            break
        Case.sleep(5)

    return out


def get_pcie_nic_ip(kvm, vm_name):
    rcode, std_out, std_err = kvm.execute_vm_cmd(vm_name, "lspci |grep -i 'Virtual Function'")
    nics = str(std_out)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')
    bdf = target_nic[0].strip()
    kvm.start_vm(vm_name)
    _, ether_name, _ = kvm.execute_vm_cmd(vm_name, f'ls /sys/bus/pci/devices/0000:{bdf}/net')
    _, res, _ = kvm.execute_vm_cmd(vm_name, f"ifconfig {ether_name.strip()}| grep -i inet | grep -v inet6")
    return res.split()[1]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")

    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_virtual_common_xmlcli'))

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel2'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("Shows the maximum number of VFs supported by a given port.")
    _, nics, _ = sut.execute_shell_cmd(f"lspci | grep -i {X710_NIC_TYPE}")
    nics = str(nics)[:-1].split('\n')
    target_nic1 = nics[0].strip().split(' ')[0].strip()
    target_nic2 = nics[1].strip().split(' ')[0].strip()
    _, ether_name1, std_err = sut.execute_shell_cmd(f'ls /sys/bus/pci/devices/0000:{target_nic1}/net')
    _, ether_name2, std_err = sut.execute_shell_cmd(f'ls /sys/bus/pci/devices/0000:{target_nic2}/net')

    code, num1, err = sut.execute_shell_cmd(f"cat /sys/class/net/{ether_name1.strip()}/device/sriov_totalvfs")
    Case.expect(f" the maximum number of VFs {num1.strip()}", err == "")
    code, num2, err = sut.execute_shell_cmd(f"cat /sys/class/net/{ether_name2.strip()}/device/sriov_totalvfs")
    Case.expect(f" the maximum number of VFs {num2.strip()}", err == "")

    Case.step(f"Create {num1.strip()} VF for each PF in terminal: ")
    code, out, err = sut.execute_shell_cmd(
        f"echo {num1.strip()} > /sys/class/net/{ether_name1.strip()}/device/sriov_numvfs")
    Case.expect(f" create {num1.strip()} VF for each PF in terminal success", err == "")

    Case.step(f"Create {num2.strip()} VF for each PF in terminal: ")
    code, out, err = sut.execute_shell_cmd(
        f"echo {num2.strip()} > /sys/class/net/{ether_name2.strip()}/device/sriov_numvfs")
    Case.expect(f" create {num2.strip()} VF for each PF in terminal success", err == "")

    Case.step("Check if * VF is created for each PF in terminal: ")
    code, v_nics, err = sut.execute_shell_cmd("lspci |grep -i 'Virtual Function'")
    Case.expect("VF have been created on unit, VFs are ready to use.", err == "")

    Case.step("Assgin the maximum number VF to VM, connect with DHCP server with PF.")
    kvm = get_vmmanger(sut)
    v_nics = str(v_nics)[:-1].split('\n')
    target_v1_nic = v_nics[0].strip().split(' ')[0]
    target_v2_nic = v_nics[-1].strip().split(' ')[0]
    static_ip_assgin(kvm, RHEL_VM_NAME, target_v1_nic)
    static_ip_assgin(kvm, RHEL_VM_NAME2, target_v2_nic)
    Case.sleep(60)

    ip1_vm = kvm.get_vm_external_ip(RHEL_VM_NAME)
    ip2_vm = kvm.get_vm_external_ip(RHEL_VM_NAME2)
    code, std_out, std_err = kvm.execute_vm_cmd(RHEL_VM_NAME, f"ping -c 4 {ip2_vm}")
    loss_data = re.search(r'(\d+)% packet loss', std_out).group(1)
    Case.expect('ping successful', int(loss_data) == 0)
    log_check.scan_format("inet %s", std_out)
    code, std_out, std_err = kvm.execute_vm_cmd(RHEL_VM_NAME2, f"ping -c 4 {ip1_vm}")
    loss_data = re.search(r'(\d+)% packet loss', std_out).group(1)
    Case.expect('ping successful', int(loss_data) == 0)
    log_check.scan_format("inet %s", std_out)

    Case.step("Restore the environment")
    kvm.shutdown_vm(RHEL_VM_NAME)
    kvm.shutdown_vm(RHEL_VM_NAME2)
    bus, slot, func = split_pci_dev_id(target_v1_nic)
    kvm.detach_nic_from_vm(RHEL_VM_NAME, bus, slot, func)
    bus, slot, func = split_pci_dev_id(target_v2_nic)
    kvm.detach_nic_from_vm(RHEL_VM_NAME2, bus, slot, func)
    sut.execute_shell_cmd('reboot')
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)


def clean_up(sut):
    if Result.returncode != 0:
        kvm = get_vmmanger(sut)
        kvm.shutdown_vm(RHEL_VM_NAME)
        kvm.shutdown_vm(RHEL_VM_NAME2)

        v_nics = sut.execute_shell_cmd("lspci |grep -i 'Virtual Function'")[1]
        v_nics = str(v_nics)[:-1].split('\n')
        target_v1_nic = v_nics[0].strip().split(' ')[0]
        target_v2_nic = v_nics[-1].strip().split(' ')[0]

        bus, slot, func = split_pci_dev_id(target_v1_nic)
        kvm.detach_nic_from_vm(RHEL_VM_NAME, bus, slot, func)
        bus, slot, func = split_pci_dev_id(target_v2_nic)
        kvm.detach_nic_from_vm(RHEL_VM_NAME2, bus, slot, func)

        sut.execute_shell_cmd('reboot')
        Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
        Case.sleep(60)

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
