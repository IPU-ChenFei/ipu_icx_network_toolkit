"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883655
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
        Plug a PCIe NIC card into SUT x710 etc.
    2. SW Configuration
         Create a centos VM
         Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Centos) Installation'
        2. Tools
        3. Files
        4. virtual machine
            linux_vm_name = 'rhel1'

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Configure PCIE Network pass-through devices on an ESXi host Procedures"
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to OS')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.check_preconditions()

    server_ip = sut.supported_os[sut.default_os].ip

    Case.step("Active one of the PCI device")
    _, nics, _ = sut.execute_shell_cmd(f"lspci | grep -i {X710_NIC_TYPE}")
    nics = str(nics)[:-1].split('\n')
    sut_id = nics[-1].strip().split(' ')[0]
    ret, res, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={sut_id} -e=on -a")
    Case.expect("hardware pci set on pass", err == '')

    Case.step("stop the vm")
    esxi = get_vmmanger(sut)
    esxi.shutdown_vm(RHEL_VM_NAME)

    Case.step("Get the Passthrough available PCI device list from the host")
    esxi.execute_host_cmd_esxi(f"$scsiDeviceList = Get-PassthroughDevice -VMHost {server_ip} -Type Pci")
    ret, res, err = esxi.execute_host_cmd_esxi(
        f"Get-PassthroughDevice -VMHost {server_ip} -Type Pci | "
        f"Where-Object {{$_.Uid -match \"'{sut_id}'\"}} | "
        r"Format-Custom -Property ExtensionData -Depth 2")
    res1 = log_check.find_lines(sut_id, res)
    Case.expect(f"We can find this {sut_id} from {res1} in the output pass", res1)

    Case.step("Build PCI device connection to VM")
    ret, res, err = esxi.execute_host_cmd_esxi(f"$scsiDeviceList = Get-PassthroughDevice -VMHost {server_ip} -Type Pci "
                                               f"| Where-Object {{$_.Uid -match '{sut_id}'}};"
                                               f"Add-PassthroughDevice -VM {RHEL_VM_NAME} -PassthroughDevice $scsiDeviceList[0]")
    Case.expect("Build PCI device connection to VM success!", err is None)

    Case.step("Centos OS SSD Passthrough requires")
    ret, res, err = esxi.execute_host_cmd_esxi("$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;"
                                               "$spec.memoryReservationLockedToMax = $true;"
                                               f"(Get-VM {RHEL_VM_NAME}).ExtensionData.ReconfigVM_Task($spec)")
    Case.expect("passthrough device set pass", ret == 0)

    Case.step("Get vm ip")
    esxi.start_vm(RHEL_VM_NAME)
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    vm_ip_list = esxi.get_vm_ip_list(RHEL_VM_NAME)
    Case.expect(f"Get {vm_ip_list} pass", len(vm_ip_list) != len(vm_ip))

    ret, res, err = esxi.execute_vm_cmd(RHEL_VM_NAME, r"lspci | grep -i ethernet")
    res1 = log_check.find_lines(X710_NIC_TYPE, res)
    Case.expect(f"show Ethernet {res1} pass", res1)

    Case.step("restore vm env")
    esxi.shutdown_vm(RHEL_VM_NAME)
    _, out, err = esxi.execute_host_cmd_esxi(
        f'Get-PassthroughDevice -VM {RHEL_VM_NAME} | Remove-PassthroughDevice -confirm:$false')
    Case.expect("restore vm successful ", err is None)
    ret, res, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={sut_id} -e=off -a")
    Case.expect("hardware pci set on pass", err == '')
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
