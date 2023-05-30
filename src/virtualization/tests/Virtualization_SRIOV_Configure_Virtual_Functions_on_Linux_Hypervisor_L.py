"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509886016
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
    "The system checks use of all supported Pagetable sizes"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)

    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)
    my_os.warm_reset_cycle_step(sut)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step('Verify the host system sees the PCI Ethernet device')
    code, out, err = sut.execute_shell_cmd('lspci | grep -i net')
    Case.expect("Verify the host system sees the PCI Ethernet device successfully and returns a zero return code",
                err == "")

    Case.step('Create Virtual Functions on SRIOV supported Ethernet Adapter')
    _, nics, _ = sut.execute_shell_cmd('lspci | grep -i {}'.format(X710_NIC_TYPE))
    nics = str(nics)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')[0]
    target_nic_full = str('0000:') + target_nic
    code, out, err = sut.execute_shell_cmd('echo 2 > /sys/bus/pci/devices/{}/sriov_numvfs'.format(target_nic_full))
    Case.expect("Create Virtual Functions on SRIOV supported Ethernet Adapter successfully", err == "")

    Case.step('Check Virtual Function')
    err = sut.execute_shell_cmd('lspci | grep -i "Virtual Function"')[2]
    Case.expect("'Check Virtual Function' successfully", err == "")

    Case.step('Start VM')
    kvm.start_vm(RHEL_VM_NAME)

    Case.step("add vf in vm")
    bus, slot, func = split_pci_dev_id(target_nic)
    kvm.attach_nic_to_vm(RHEL_VM_NAME, bus, slot, func)
    kvm.execute_vm_cmd(RHEL_VM_NAME, 'lspci | grep -i {}'.format(X710_NIC_TYPE))
    kvm.reboot_vm(RHEL_VM_NAME)

    Case.step("get and ping VM ip")
    vm_ip = kvm.get_vm_ip_list(RHEL_VM_NAME)[0]
    ping_res = kvm.ping_vm(vm_ip)
    Case.expect("ping VM successfully", ping_res)

    Case.step("remove vm network")
    kvm.shutdown_vm(RHEL_VM_NAME)
    kvm.detach_nic_from_vm(RHEL_VM_NAME, bus, slot, func)

    Case.step("remove vf")
    code, out, err = sut.execute_shell_cmd('echo 0 > /sys/bus/pci/devices/{}/sriov_numvfs'.format(target_nic_full))
    Case.expect("Remove Virtual Functions on SRIOV supported Ethernet Adapter successfully", err == "")


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
