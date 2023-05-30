"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883530
 @Author:
 @Prerequisite:
    1. HW Configuration
        1. A X710 network card plug in PCIe, connect to external network with port 0
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
    'Test passthrough Network to VM and IO access capability using a PCIe Gen 3.0 NIC card.'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)

    Case.prepare("boot to os")
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_security_common_xmlcli'))

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1', True))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.prepare("echo intel_iommu=on iommu=pt in sut")
    err = sut.execute_shell_cmd('grubby --update-kernel=ALL --args="intel_iommu=on"')[2]
    Case.expect("grubby iommu pass", err == '')
    ret = sut.execute_shell_cmd('grub2-mkconfig -o /boot/grub2/grub.cfg iommu=pt')[0]
    Case.expect("grub2-mkconfig pass", ret == 0)
    Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)

    Case.step("get NIC bus information")
    _, std_out, _ = sut.execute_shell_cmd('lspci | grep {}'.format(X710_NIC_TYPE))
    nic_lines = std_out.strip().splitlines()
    target_nic = nic_lines[0]
    target_nic_id = target_nic.split()[0]
    kvm.start_vm(RHEL_VM_NAME)

    Case.step("attach pci network card and reboot VM")
    bus, slot, func = split_pci_dev_id(target_nic_id)
    kvm.attach_nic_to_vm(RHEL_VM_NAME, bus, slot, func)
    kvm.reboot_vm(RHEL_VM_NAME)

    Case.step("check vm network is fine")
    ret = kvm.execute_vm_cmd(RHEL_VM_NAME, "lspci | grep -i net")[1]
    keyword = log_check.find_keyword(X710_NIC_TYPE, ret)
    Case.expect(f"{ret} is exsit", keyword)
    ret = kvm.execute_vm_cmd(RHEL_VM_NAME, "ifconfig")[1]
    Case.expect(f"{ret}", ret)

    kvm.detach_nic_from_vm(RHEL_VM_NAME, bus, slot, func)
    kvm.shutdown_vm(RHEL_VM_NAME)


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
