"""
@Case Link: https://hsdes.intel.com/appstore/article/#/1509884582
@Author:Liu, JianjunX
@Prerequisite:
1. HW Configuration
    Have an external NIC card with two ports and SR-IOV support plugged into SUT
2. SW Configuration
    Set up iSCSI storage network and connect to it from SUT
    1. Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
    2.  Create a centos VM
        Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Centos) Installation'
    3. Tools
    4. Files
    5. virtual machine
            linux_vm_name = 'rhel1'
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Purpose of this test case is to verify the pass through of gen 4.0 card in esxi OS."
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to uefi shell")
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.check_preconditions()

    Case.step("Verify Network Connectivity for : OS Management Network")
    esxi = get_vmmanger(sut)
    Case.expect("Successfully SSHed into SUT.", True)

    esxi.start_vm(RHEL_VM_NAME)
    Case.step("Verify Network Connectivity for : VM Traffic")
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    code, out, err = sut.execute_shell_cmd(f"ping {vm_ip}")
    Case.expect(" Ping VM successfully.", err == "")

    Case.step("Verify Network Connectivity for : iSCSI Storage Network")
    code, out, err = sut.execute_shell_cmd("esxcli iscsi session connection list")
    Case.expect("The iSCSI target is present.", err == "")


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
