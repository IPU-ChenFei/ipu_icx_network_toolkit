"""
@Case Link: https://hsdes.intel.com/appstore/article/#/1509884562
@Author:Liu, JianjunX
@Prerequisite:
1. HW Configuration
   Plug a PCIe 4.0 NIC card into SUT
2. SW Configuration
    1. Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
    2.  Create a centos VM
        Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Centos) Installation'
    4. Tools

    5. Files
    6. virtual machine
        linux_vm_name = 'rhel1'
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Purpose of this test case is to verify the pass through of gen 4.0 card in esxi OS."
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to uefi shell ")
    server_ip = sut.supported_os[sut.default_os].ip
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(NicPrecondition(sut, 'MLX NIC', 'Mell'))
    Case.check_preconditions()

    Case.step("Enable device passthrough in ESXi:")
    code, devs, err = sut.execute_shell_cmd(f"lspci | grep -i {MLX_NIC_TYPE}")
    dev_id = log_check.scan_format("%s ", devs)[0]
    code, out, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={dev_id} -e=on -a")
    Case.expect("The device is configured to passthru.", err == "")
    #
    esxi = get_vmmanger(sut)
    Case.step("Assign passthrough device to VM:")
    esxi.shutdown_vm(RHEL_VM_NAME)
    _, out, err = esxi.execute_host_cmd_esxi(
        f'Get-PassthroughDevice -VM {RHEL_VM_NAME} | Remove-PassthroughDevice -confirm:$false')
    code, out, err = esxi.execute_host_cmd_esxi(f"$devs=Get-PassthroughDevice -VMHost {server_ip} "
                                                fr"| Where-Object {{($_.Name -like \"*{MLX_NIC_TYPE}*\") -or ("
                                                fr"$_.VendorName -match \"{MLX_NIC_TYPE}\")}}; "
                                                f"Add-PassthroughDevice -VM {RHEL_VM_NAME} -PassthroughDevice $devs[0]; "
                                                r"$spec=New-Object VMware.Vim.VirtualMachineConfigSpec; "
                                                r"$spec.memoryReservationLockedToMax=$true;"
                                                fr"(Get-VM {RHEL_VM_NAME}).ExtensionData.ReconfigVM_Task($spec)")
    Case.expect("A Mellanox ConnectX-5 network adapater has been used here.", err is None)

    Case.step("Verify that the Network Adapter has been successfully passthroughed to VM:")
    esxi.start_vm(RHEL_VM_NAME)
    code, out, err = esxi.execute_vm_cmd(RHEL_VM_NAME, f"lspci | grep -i {MLX_NIC_TYPE}")
    # check log
    result = log_check.find_lines(MLX_NIC_TYPE, out)
    Case.expect("test success", len(result) != 0)

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
