"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509886148
 @Author:
 @Prerequisite:
    1. HW Configuration
        1. A Mellanox network card plug in PCIe, connect to external network with port 0
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
            1. /home/BKCPkg/domainx/virtualization/tools/vfio-pci-bind.sh copy from
              \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\tools\vfio-pci-bind.sh
              Use command chmod a+x and dos2unix to handle it
        3. Files
            1. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
    3. Virtual Machine
        1. A Linux virtual machine named "rhel1"
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Test passthrough Network to VM and IO access capability using a PCIe Gen 4.0 NIC card.'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare("boot to os with bios knobs")
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_virtual_common_xmlcli'))

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("echo intel_iommu=on iommu=pt in sut")
    err = sut.execute_shell_cmd('grubby --update-kernel=ALL --args="intel_iommu=on"')[2]
    Case.expect("grubby iommu pass", err == '')
    ret = sut.execute_shell_cmd('grub2-mkconfig -o /boot/grub2/grub.cfg iommu=pt')[0]
    Case.expect("grub2-mkconfig pass", ret == 0)
    my_os.warm_reset_cycle_step(sut)

    kvm = get_vmmanger(sut)
    Case.step("check network id and fine")
    _, nics, _ = sut.execute_shell_cmd('lspci | grep -i {}'.format(MLX_NIC_TYPE))
    nics = str(nics)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')[0]
    err = sut.execute_shell_cmd(f" lspci -n -s {target_nic} -vvv | grep -i lnk")[2]
    Case.expect("check lnk pass", err == '')

    Case.step("Bind the NIC to vfio")
    ret = sut.execute_shell_cmd(f"./vfio-pci-bind.sh {target_nic}", cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))[0]
    Case.expect("bind network successfully", ret == 0)

    Case.step("Double check vfio")
    ret = sut.execute_shell_cmd(f"lspci -s {target_nic} -k")[1]
    ret = log_check.find_keyword("vfio-pci", ret)
    Case.expect(f"The Kernel driver in use: {ret}", ret)

    Case.step("Start VM")
    bus, slot, func = split_pci_dev_id(target_nic)
    kvm.attach_nic_to_vm(RHEL_VM_NAME, bus, slot, func)
    kvm.start_vm(RHEL_VM_NAME)
    Case.sleep(120)

    Case.step("check vm network is fine")
    ret = kvm.execute_vm_cmd(RHEL_VM_NAME, "lspci | grep -i net")[1]
    ret = log_check.find_keyword(MLX_NIC_TYPE, ret)
    Case.expect(f"{ret} is exsit", ret)
    ret = kvm.execute_vm_cmd(RHEL_VM_NAME, "ifconfig")[1]
    Case.expect(f"{ret}", ret)

    Case.step("remove vm network")
    kvm.shutdown_vm(RHEL_VM_NAME)
    kvm.detach_nic_from_vm(RHEL_VM_NAME, bus, slot, func)


def clean_up(sut):
    if Result.returncode != 0:
        if Case.step_count >= 5:
            _, nics, _ = sut.execute_shell_cmd('lspci | grep -i {}'.format(MLX_NIC_TYPE))
            nics = str(nics)[:-1].split('\n')
            target_nic = nics[0].strip().split(' ')[0]
            bus, slot, func = split_pci_dev_id(target_nic)
            kvm = get_vmmanger(sut)
            kvm.shutdown_vm(RHEL_VM_NAME)
            kvm.detach_nic_from_vm(RHEL_VM_NAME, bus, slot, func)
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
