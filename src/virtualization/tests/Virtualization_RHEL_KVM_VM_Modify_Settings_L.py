"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509886067
 @Author:
 @Prerequisite:
    1. HW Configuration
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
    'The purpose of this test case is making sure Virtual Machine settings can be modified using command line tool.'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)

    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("set vm autostart")
    kvm.start_vm(RHEL_VM_NAME)
    kvm.set_vm_autostart(RHEL_VM_NAME)
    is_autostart = kvm.is_vm_autostart(RHEL_VM_NAME)
    Case.expect(f"{RHEL_VM_NAME} set to autostart successfully", is_autostart)

    kvm.set_vm_unautostart(RHEL_VM_NAME)

    Case.step("change vm memory")
    kvm.set_vm_memory(RHEL_VM_NAME, 4000)
    memory = kvm.get_vm_memory(RHEL_VM_NAME)
    Case.expect(f"{RHEL_VM_NAME} memory was set to 4000M", memory == 4000)

    kvm.shutdown_vm(RHEL_VM_NAME)


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
