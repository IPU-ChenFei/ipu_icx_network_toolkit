"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883475
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
        In order to not lose the connection to ESXi host,
        need to plug an extra NIC card into SUT (I210)
    2. SW Configuration
        Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
        Create a Centos VM
        2. Tools
        3. Files
        4. virtual machine
            linux_vm_name = 'rhel1'

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Configure LOM pass-through devices on an ESXi host Procedures."
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to OS')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    server_ip = sut.supported_os[sut.default_os].ip

    Case.step("Enable device passthrough in ESXI")
    _, nics, _ = sut.execute_shell_cmd(f"lspci | grep -i {I210_NIC_TYPE}")
    nics = str(nics)[:-1].split('\n')
    sut_id = nics[0].strip().split(' ')[0]
    Case.expect(f"exist {I210_NIC_TYPE}", sut_id != "")
    ret, res, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={sut_id} -e=on -a")
    Case.expect("hardware pci set on pass", err == '')

    Case.step("Assign passthrough device to VM")
    esxi = get_vmmanger(sut)
    esxi.shutdown_vm(RHEL_VM_NAME)
    _, out, err = esxi.execute_host_cmd_esxi(
        f'Get-PassthroughDevice -VM {RHEL_VM_NAME} | Remove-PassthroughDevice -confirm:$false')

    ret, res, err = esxi.execute_host_cmd_esxi(
        f'$devs = Get-PassthroughDevice -VMHost {server_ip}| Where-Object {{$_.Name -like \\"*{I210_NIC_TYPE}*\\"}};'
        f"Add-PassthroughDevice -VM {RHEL_VM_NAME} -PassthroughDevice $devs[0]")
    Case.expect("pass through device pass", ret == 0)
    ret, res, err = esxi.execute_host_cmd_esxi("$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;"
                                               "$spec.memoryReservationLockedToMax = $true;"
                                               f"(Get-VM {RHEL_VM_NAME}).ExtensionData.ReconfigVM_Task($spec)")
    Case.expect("passthrough device set pass", ret == 0)

    Case.step('Verify that the Network Adapter has been successfully passthroughed to VM')
    esxi.start_vm(RHEL_VM_NAME)
    Case.sleep(60)
    ret, res, err = esxi.execute_vm_cmd(RHEL_VM_NAME, "lspci | grep -i ethernet | grep -v VMXNET3")
    Case.expect(f"show Ethernet {res} pass", res != "")

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
