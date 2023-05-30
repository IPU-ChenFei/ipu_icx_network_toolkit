"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883512
 @Author:
 @Prerequisite:
    1. HW Configuration
        1. A X710 network card plug in PCIe, connect to external network with port 0 and port1
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
            1. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
            2. vfio-pci-bind.sh copy to home/BKCPkg/domains/virtualization/
            3. /home/BKCPkg/domains/virtualization/IMGS/cent0.qcow2 is need
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Verify virtual OS(Linux and Windows) basic functionality through KVM console."
]


def dhcp_ip_assgin(kvm, vm_name):
    rcode, std_out, std_err = kvm.execute_vm_cmd(vm_name, "lspci |grep -i 'Virtual Function'")
    nics = str(std_out)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')
    bdf = target_nic[0].strip()
    out = ""
    kvm.execute_vm_cmd(vm_name, f'dhclient -r && dhclient')

    _, ether_name, std_err = kvm.execute_vm_cmd(vm_name, f'ls /sys/bus/pci/devices/0000:{bdf}/net')
    for i in range(10):
        _, out, std_err = kvm.execute_vm_cmd(vm_name, f"ifconfig {ether_name}")
        if len(log_check.find_lines("inet", out)) != 0:
            out = log_check.scan_format("inet %s", out)[0]
            break
        Case.sleep(5)

    return out


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare("boot to os")
    # boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_virtual_common_xmlcli'))

    # Case.step("set iommu")
    # ret = sut.execute_shell_cmd('grubby --update-kernel=ALL '
    #                             '--args="intel_iommu=on,sm_on iommu=pt"')[0]
    # Case.expect("set iommu pass", ret == 0)
    # my_os.warm_reset_cycle_step(sut)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'cent0.img', sut_tool('VT_QEMU_CENT_TEMPLATE_L')))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("set up virtual")
    Case.sleep(15)
    _, nics, _ = sut.execute_shell_cmd(f'lspci | grep -i {X710_NIC_TYPE}')
    nics = str(nics)[:-1].split('\n')
    sut_id1 = nics[0].strip().split(' ')[0]
    sut_id2 = nics[1].strip().split(' ')[0]
    ret = sut.execute_shell_cmd('echo 1 > /sys/bus/pci/devices/0000:{}/sriov_numvfs'.format(sut_id1))[0]
    Case.expect('echo network successfully', ret == 0)
    ret = sut.execute_shell_cmd('echo 1 > /sys/bus/pci/devices/0000:{}/sriov_numvfs'.format(sut_id2))[0]
    Case.expect('echo network successfully', ret == 0)

    Case.step("set environment")
    _, nics, _ = sut.execute_shell_cmd('lspci | grep -i Virtual')
    nics = str(nics)[:-1].split('\n')
    en1 = nics[0].strip().split(' ')[0]
    en2 = nics[1].strip().split(' ')[0]
    sut.execute_shell_cmd("modprobe vfio-pci")
    out = sut.execute_shell_cmd(f"lspci -n| grep -i {en1}|awk '{{print $3}}'")[1].replace(":", " ").strip()
    ret = sut.execute_shell_cmd(f'echo "{out}" > /sys/bus/pci/drivers/vfio-pci/new_id')[0]
    Case.expect("echo pass", ret == 0)
    sut.execute_shell_cmd(f"echo 0000:{en1} > /sys/bus/pci/devices/0000:{en1}/driver/unbind")
    sut.execute_shell_cmd(f"echo 0000:{en2} > /sys/bus/pci/devices/0000:{en2}/driver/unbind")
    sut.execute_shell_cmd(f"echo 0000:{en1} > /sys/bus/pci/drivers/vfio-pci/bind")
    sut.execute_shell_cmd(f"echo 0000:{en2} > /sys/bus/pci/drivers/vfio-pci/bind")

    Case.step("start vm1 vm2")
    ret = sut.execute_shell_cmd(f"sh vfio-pci-bind.sh {en1}", cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))[0]
    Case.expect("unbind net", ret == 0)
    ret = sut.execute_shell_cmd(f"sh vfio-pci-bind.sh {en2}", cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))[0]
    Case.expect("unbind net", ret == 0)

    Case.step("create vm1 vm2")
    qemuhypervisor = QemuHypervisor(sut)
    qemuhypervisor.create_vm_from_template(CENT_VM_NAME, QEMU_CENT_TEMPLATE, bios=VT_OVMF_L)
    qemuhypervisor.create_vm_from_template(CENT_VM_NAME2, QEMU_CENT_TEMPLATE, bios=VT_OVMF_L)
    qemuhypervisor.attach_acce_dev_to_vm(CENT_VM_NAME, dev_list=[en1])
    qemuhypervisor.attach_acce_dev_to_vm(CENT_VM_NAME2, dev_list=[en2])
    qemuhypervisor.start_vm_debug(CENT_VM_NAME, 2222)
    qemuhypervisor.start_vm_debug(CENT_VM_NAME2, 2223)
    code, out, err = qemuhypervisor.execute_vm_cmd(CENT_VM_NAME, "lspci | grep -i Virtual")
    Case.expect("check vf success", out.strip() != "")
    code, out, err = qemuhypervisor.execute_vm_cmd(CENT_VM_NAME2, "lspci | grep -i Virtual")
    Case.expect("check vf success", out.strip() != "")
    ip1 = dhcp_ip_assgin(qemuhypervisor, CENT_VM_NAME)
    ip2 = dhcp_ip_assgin(qemuhypervisor, CENT_VM_NAME2)
    Case.step("sut ping  vm")
    ret = sut.execute_shell_cmd(f"ping -c 4 {ip1}")[0]
    Case.expect(f"sut ping {ip1} pass", ret == 0)
    ret = sut.execute_shell_cmd(f"ping -c 4 {ip2}")[0]
    Case.expect(f"sut ping {ip2} pass", ret == 0)

    Case.step(" vm1 ping  vm2")
    ret = qemuhypervisor.execute_vm_cmd(CENT_VM_NAME, f"ping -c 4 {ip2}")[0]
    Case.expect("ping pass ip2", ret == 0)
    ret = qemuhypervisor.execute_vm_cmd(CENT_VM_NAME2, f"ping -c 4 {ip1}")[0]
    Case.expect("ping pass ip1", ret == 0)
    qemuhypervisor.shutdown_vm(CENT_VM_NAME)
    qemuhypervisor.shutdown_vm(CENT_VM_NAME2)


def clean_up(sut):
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
