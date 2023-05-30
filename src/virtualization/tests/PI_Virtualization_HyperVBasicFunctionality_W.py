"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883340
 @Author:
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
            1. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
            2. Windows virtual machine named "windows1"
            3. RHEL virtual machine named "rhel1"
"""

from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Configuration:1.BIOS Setting:EDKII Menu -- Socket Configuration -- Processor Configuration -- VMX -> Enable '
    'EDKII Menu -- Socket Configuration -- IIO Configuration ?Intel@ VT for Directed I/O(VT-d) -- Intel@ VT for Directed I/O -> Enable',
    '2.Install Hyper-V (Refer to Virtualization - Hyper-V - Install Hypervisor)'
    '3. Create a windows VM and a linux VM (Refer to Virtualization - Hyper-V - Guest OS Install & Config)'
]


def test_steps(sut, my_os):

    Case.prepare('boot to OS')
    hyperv = get_vmmanger(sut)
    boot_to(sut, sut.default_os)

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.check_preconditions()

    repeat_times = 1
    for vm in [WINDOWS_VM_NAME, RHEL_VM_NAME]:
        Case.step('ping VM successfully after reboot SUT')
        for i in range(repeat_times):
            my_os.warm_reset_cycle_step(sut)
            Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)
            time.sleep(30)
            hyperv.start_vm(vm, 600)
            vm_ip = hyperv.get_vm_ip(vm, SWITCH_NAME)
            hyperv.ping_vm(vm_ip)

        Case.step('shutdown and power up SUT, then boot the Virtual Machine and check whether it is working')
        for i in range(repeat_times):
            my_os.g3_cycle_step(sut)
            Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)
            time.sleep(30)
            hyperv.start_vm(vm, 600)
            vm_ip = hyperv.get_vm_ip(vm, SWITCH_NAME)
            hyperv.ping_vm(vm_ip)

        Case.step('reboot virtual machine , to check Virtual Machine works')
        for i in range(repeat_times):
            Case.sleep(30)
            hyperv.reboot_vm(vm, 600)
            time.sleep(30)
            vm_ip = hyperv.get_vm_ip(vm, SWITCH_NAME)
            hyperv.ping_vm(vm_ip)

        Case.step('Shutdown and power up virtual machine , to check Virtual Machine works. ')
        for i in range(repeat_times):
            hyperv.shutdown_vm(vm, 600)
            hyperv.start_vm(vm, 600)
            time.sleep(30)
            vm_ip = hyperv.get_vm_ip(vm, SWITCH_NAME)
            hyperv.ping_vm(vm_ip)

        Case.step('Shutdown VM and remove VM switch network adapter')
        hyperv.shutdown_vm(vm, 600)


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
