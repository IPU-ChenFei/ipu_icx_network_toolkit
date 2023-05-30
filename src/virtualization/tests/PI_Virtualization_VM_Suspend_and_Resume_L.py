"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883852
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
     3. Virtual Machine
        1. A Linux virtual machine named "rhel1"
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "The system checks use of all supported Pagetable sizes"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)

    logger.info("I am logger")
    Case.prepare(f"boot to {sut.default_os}")
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step('Start VM')
    kvm.start_vm(RHEL_VM_NAME)

    Case.step('Suspend VM')
    kvm.suspend_vm(RHEL_VM_NAME)

    Case.step('Resume VM')
    kvm.resume_vm(RHEL_VM_NAME)

    kvm.shutdown_vm(RHEL_VM_NAME)


def clean_up(sut):
    if Result.returncode != 0:
        kvm = get_vmmanger(sut)
        try:
            kvm.shutdown_vm(RHEL_VM_NAME)
        except:
            pass
        cleanup.to_s5(sut)


def test_main():
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
