"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509876227
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
        4. virtual machine
            linux_vm_name = 'rhel1'
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Verify virtualization Linux OS is workable after reboot."
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to uefi shell')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1', True))
    Case.check_preconditions()

    Case.step('Operate in Powershell CLI')
    esxi = get_vmmanger(sut)
    esxi.start_vm(RHEL_VM_NAME)
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    Case.expect(f"Get {vm_ip} pass", vm_ip)
    ret, res, err = esxi.execute_vm_cmd(RHEL_VM_NAME, r'sed -i \"s/#WaylandEnable=false/#WaylandEnable=false\r\nAutomaticLoginEnable=True\r\nAutomaticLogin=root\r\n/g\" /etc/gdm/custom.conf')
    Case.expect("Vim to the custom.conf pass", ret == 0)

    Case.step("reboot vm 5 times")
    for i in range(5):
        esxi.reboot_vm(RHEL_VM_NAME)
        Case.sleep(40)
        vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
        Case.expect(f"Get {vm_ip} pass", vm_ip)


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
