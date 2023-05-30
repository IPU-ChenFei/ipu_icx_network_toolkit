"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509918181
 @Author:
 @Prerequisite:
    1. HW Configuration
        1. need a nvme ssd Plug in PCIE
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
    'attach disk, detach disk'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)

    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1', True))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("create disk img")
    kvm.create_disk_file(disk_path=NEW_IMG_PATH, disk_size_gb=20)

    Case.step("Display VM block device list")
    vm_disk_list = kvm.get_vm_disk_list(f"{RHEL_VM_NAME}")
    vm_disk_list.sort()
    last_disk_name = vm_disk_list[-1]
    drive_letters = ['vda', 'vdb', 'vdc', 'vdd', 'vde']
    if last_disk_name not in drive_letters:
        new_disk_name = drive_letters[0]
    else:
        new_disk_name = drive_letters[drive_letters.index(last_disk_name) + 1]

    Case.step("attach disk")

    kvm.attach_disk_to_vm(RHEL_VM_NAME, NEW_IMG_PATH, new_disk_name)
    kvm.start_vm(RHEL_VM_NAME)
    std_out = kvm.execute_vm_cmd(RHEL_VM_NAME, "lsblk")[1]
    is_disk_exist = log_check.find_lines(new_disk_name, std_out)
    Case.expect(f"{new_disk_name} is exist", is_disk_exist)

    Case.step("detach disk")
    kvm.detach_disk_from_vm(RHEL_VM_NAME, new_disk_name)
    std_out = kvm.execute_vm_cmd(RHEL_VM_NAME, "lsblk")[1]
    is_disk_exist = log_check.find_lines(new_disk_name, std_out)
    Case.expect(f"{new_disk_name} is not exist", not is_disk_exist)

    sut.execute_shell_cmd(f"rm -f {NEW_IMG_PATH}")
    kvm.shutdown_vm(RHEL_VM_NAME)


def clean_up(sut):
    if Result.returncode != 0:
        kvm = get_vmmanger(sut)
        try:
            kvm.shutdown_vm(RHEL_VM_NAME)
            # kvm.undefine_vm(RHEL_VM_NAME)
        except:
            pass
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
