"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883551
 @Author: Han, Yufeng
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. Install a windows virtual machine named "windows1"
        2. copy "\\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\\auto-poc.zip" to
           "C:\\BKCPkg\\domains\\virtualization" and unzip it
        3. Install updated pip and paramiko
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Configuration:1.BIOS Setting:EDKII Menu -- Socket Configuration -- Processor Configuration -- VMX -> Enable '
    'EDKII Menu -- Socket Configuration -- IIO Configuration ?Intel@ VT for Directed I/O(VT-d)'\
    ' -- Intel@ VT for Directed I/O -> Enable',
    '2.Install Hyper-V (Refer to Virtualization - Hyper-V - Install Hypervisor)'
    '3. Connect an external Ethernet Network Adapter to SUT'
    '4.Create a windows VM(Refer to Virtualization - Hyper-V - Guest OS Install & Config)'
]


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    hyperv = get_vmmanger(sut)
    boot_to(sut, sut.default_os)

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1', True))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.check_preconditions()

    Case.step('Start VM')
    hyperv.start_vm(WINDOWS_VM_NAME, 600)

    Case.step('ping VM ip')
    sut.execute_shell_cmd(f'Get-VMNetworkAdapter -VMName {WINDOWS_VM_NAME} | select ipaddresses', powershell=True, timeout=60)
    vm_ip = hyperv.get_vm_ip(WINDOWS_VM_NAME, SWITCH_NAME)
    hyperv.ping_vm(vm_ip)

    Case.step('Shutdown VM and remove VM switch network adapter')
    hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)


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
