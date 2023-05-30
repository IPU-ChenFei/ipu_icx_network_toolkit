"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509881957
 @Author:Liu, JianjunX
 @Prerequisite:
    1. HW Configuration
        1. Plug a PCIe SSD into SUT
    2. SW Configuration
        1. Install Power CLI on local Windows host
            Install-Module VMware.PowerCLI -Force
        2. Create a centos VM
            Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Centos) Installation'
        2. Tools
        3. Files

        4. virtual machine
            linux_vm_name = 'rhel1'

"""

from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Configure a PCI device on a virtual machine'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare("boot to uefi_shell")

    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(DiskPrecondition(sut, 'NVME SSD', 'NVM'))
    Case.check_preconditions()

    server_ip = sut.supported_os[sut.default_os].ip
    Case.step("Find a PCI device:")
    code, devs, err = sut.execute_shell_cmd(f"lspci | grep -i {PCI_NVM_TYPE}")
    Case.expect(f"pci NVME SSD output results:[{devs}]", devs != "")
    Case.step("Active the PCI device:")
    dev_id = log_check.scan_format("%s ", devs)[0]
    code, out, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={dev_id} -e=on  -a")
    Case.expect("The device is configured to passthru.", err == "")
    esxi = get_vmmanger(sut)
    Case.step("View the status of the virtual machine: ")
    code, out, err = esxi.execute_host_cmd_esxi(f"Get-VM {RHEL_VM_NAME}")
    Case.expect("get vm status successful", err is None)
    if log_check.find_keyword("PoweredOff", out) == "":
        Case.step("Power off the Virtual Machine:")
        esxi.shutdown_vm(RHEL_VM_NAME)
        Case.expect("stop vm is successful ! ", True)

    Case.step("Get the Passthrough available device list from the host:")
    code, out, err = esxi.execute_host_cmd_esxi(f'Get-PassthroughDevice -VMHost {server_ip} | '
                                                f'Where-Object {{$_.Uid -match \\"{dev_id}\\"}}', timeout=60 * 3)
    Case.expect("Get the Passthrough devices successful!", err is None)

    Case.step("Get the Passthrough available PCI device list from the host and build PCI device connection to VM:")
    """
        $scsiDeviceList = Get-PassthroughDevice -VMHost <server_ip> -Type Pci
        $scsiDeviceList
    """
    _, out, err = esxi.execute_host_cmd_esxi(
        f'Get-PassthroughDevice -VM {RHEL_VM_NAME} | Remove-PassthroughDevice -confirm:$false')

    _, out, err = esxi.execute_host_cmd_esxi(f'$scsiDeviceList=Get-PassthroughDevice -VMHost {server_ip} '
                                             f'-Type Pci | Where-Object{{$_.Uid -match \\"{dev_id}\\"}};'
                                             f'Add-PassthroughDevice -VM {RHEL_VM_NAME} -PassthroughDevice $scsiDeviceList[0];'
                                             f'echo $scsiDeviceList[0]',
                                             timeout=60 * 3)
    Case.expect("PCI device connection to VM successful!", err is None)

    Case.step(
        'Centos OS SSD Passthrough requires "Reserve all guest memory"(All Locked), use the command below to select:')
    _, out, err = esxi.execute_host_cmd_esxi("$spec=New-Object VMware.Vim.VirtualMachineConfigSpec;"
                                             "$spec.memoryReservationLockedToMax = $true;"
                                             f"(Get-VM {RHEL_VM_NAME}).ExtensionData.ReconfigVM_Task($spec)")
    Case.expect("setting Reserve all guest memory successful!", err is None)
    Case.step("Get the ip of VM and Start Virtual Machine:")
    esxi.start_vm(RHEL_VM_NAME)
    Case.expect(" Start Virtual Machine successful!", True)

    Case.step("Get the IP Address of Virtual Machine:")
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    Case.expect(f"get the vm ip successful [{vm_ip}] ", vm_ip != "")
    Case.step("Operate in SSH connect vm and Check the PCI device::")
    rcode, std_out, std_err = esxi.execute_vm_cmd(RHEL_VM_NAME, f"lspci | grep -i {PCI_NVM_TYPE}")
    Case.expect("PCI devices can be displayed normally", std_out != "")

    Case.step("restore vm env")
    esxi.shutdown_vm(RHEL_VM_NAME)
    _, out, err = esxi.execute_host_cmd_esxi(
        f'Get-PassthroughDevice -VM {RHEL_VM_NAME} | Remove-PassthroughDevice -confirm:$false')
    Case.expect("restore vm successful ", err is None)
    code, out, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={dev_id} -e=off -a")
    Case.expect("The device is configured to passthru.", err == "")
    sut.execute_shell_cmd('reboot')
    Case.sleep(60*3)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)


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
