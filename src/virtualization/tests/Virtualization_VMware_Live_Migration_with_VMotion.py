"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509885978
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
        2 SUTs
        2 NICS required for each SUT, one for OS management &VM traffic and the second one for iSCSi storage traffic.
        See case pre_condition for specific conditions
        etc.
    2. SW Configuration
        create a vsphere server
        vsphere connected sut1 and sut2
        1. SUT Python package

        2. Tools
        3. Files
        4. virtual machine
            linux_vm_name1 = 'rhel2'
    3. case parameter example:
        eg:
        --sut=C:\Testing\FrameworkBuilds\virtualization_esxi_0507\virtualization_esxi_0507\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\virtualization\lib\tools\sut.ini
        --sut=C:\Testing\FrameworkBuilds\virtualization_esxi_0507\virtualization_esxi_0507\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\virtualization\lib\tools\sut2.ini
        --sut=C:\Testing\FrameworkBuilds\virtualization_esxi_0507\virtualization_esxi_0507\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\virtualization\lib\tools\vsphere_sut.ini

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Test live migration of a VM from a server to another server using external "
    "shared SAN stroage and/or iSCSI storage."
    "sut1.ini is the local setting, sut2.ini is the vSphere setting, "
    "sut3.ini is the second SUT setting"
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None
    Case.prepare('boot to uefi shell')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    set_bios_knobs_step(sut, *bios_knob('enable_sriov_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'Vsphere'))
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel2'))
    Case.check_preconditions()

    sut1 = sut
    sut2 = get_sut_list()[1]
    sut3 = get_sut_list()[2]
    Case.step("Connect to server: ")
    Vphere = get_vmmanger(sut3)
    esxi3 = get_vmmanger(sut)

    Case.step('check Power-on and Boot into the Operating System')
    esxi3.start_vm(Vsphere)
    Case.sleep(600)

    server1_ip = sut1.ssh_sutos._ip
    server2_ip = sut2.ssh_sutos._ip

    ret, res, err = Vphere.execute_host_cmd_esxi(f"Get-VM -Name {RHEL_VM_NAME2} | Move-VM -Destination {server1_ip}",
                                                 timeout=15 * 60)
    Case.expect("move vm ip pass", ret == 0)

    for i in range(3):
        ret, res, err = Vphere.execute_host_cmd_esxi(f"Get-VM -Name {RHEL_VM_NAME2} | Move-VM -Destination {server1_ip}",
                                                     timeout=15 * 60)
        Case.expect("Move server1 ip pass", err is None)
        ret, res, err = Vphere.execute_host_cmd_esxi(f"Get-VM -Name {RHEL_VM_NAME2} | Move-VM -Destination {server2_ip}",
                                                     timeout=15 * 60)
        Case.expect("Move server2 ip pass", err is None)

    Case.step("restore")
    ret, res, err = Vphere.execute_host_cmd_esxi(f"Get-VM -Name {RHEL_VM_NAME2} | Move-VM -Destination {server1_ip}",
                                                 timeout=15 * 60)
    Case.expect("Move server1 ip pass", err is None)


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
        # clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
