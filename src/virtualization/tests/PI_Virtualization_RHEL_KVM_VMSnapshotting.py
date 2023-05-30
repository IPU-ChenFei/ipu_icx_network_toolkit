"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883964
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
        1. A Linux virtual machine named "rhel1
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "The system checks use of all supported Pagetable sizes"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)
    snapshot_name = f'snapshot_{int(time.time())}'

    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1', True))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step('Start VM')
    kvm.start_vm(RHEL_VM_NAME)

    Case.step('Create a file in VM via SSH')
    test_txt = 'test.txt'
    kvm.execute_vm_cmd(RHEL_VM_NAME, f"mkdir -p {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}")
    kvm.execute_vm_cmd(RHEL_VM_NAME, f"echo \"This_is_a_Test\" >> {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/{test_txt}")
    _, out, _ = kvm.execute_vm_cmd(RHEL_VM_NAME, f"ls {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}")
    keyword = log_check.find_keyword(test_txt, out)
    Case.expect(f"{keyword} is exist", keyword != "")

    Case.step('Generate Snapshot')
    kvm.create_vm_snapshot(RHEL_VM_NAME, snapshot_name)
    snap_list = kvm.get_vm_snapshot_list(RHEL_VM_NAME)
    Case.expect("create snapshot succeed", snapshot_name in snap_list)

    Case.step('Delete the file in VM via SSH session')
    kvm.execute_vm_cmd(RHEL_VM_NAME, f"rm -f {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/{test_txt}")
    code, out, err = kvm.execute_vm_cmd(RHEL_VM_NAME, f"ls {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}")
    out = log_check.find_lines(test_txt, out)
    Case.expect(f"{test_txt} is not exist", not out)

    Case.step('Restore the snapshot')
    kvm.shutdown_vm(RHEL_VM_NAME)
    kvm.restore_vm_snapshot(RHEL_VM_NAME, snapshot_name)
    Case.sleep(60)

    Case.step("SSH to VM show 'test.txt'")
    code, out, err = kvm.execute_vm_cmd(RHEL_VM_NAME, f"ls {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}")
    keyword = log_check.find_lines(test_txt, out)
    Case.expect(f"{out} is exist", keyword)

    Case.step("Delete snapshot")
    kvm.delete_vm_snapshot(RHEL_VM_NAME, snapshot_name)
    snap_list = kvm.get_vm_snapshot_list(RHEL_VM_NAME)
    Case.expect("delete snapshot succeed", snapshot_name not in snap_list)

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
