"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509888687
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
    'Test that the guest OS passes local storage tests.'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    kvm = get_vmmanger(sut)

    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)

    Case.step("Display VM block device list")
    kvm.start_vm(RHEL_VM_NAME)
    std_out = kvm.execute_vm_cmd(RHEL_VM_NAME, "lsblk -l")[1]
    if "sda" in std_out:
        last_disk_name = "sda"
    elif "vda" in std_out:
        last_disk_name = "vda"
    else:
        raise Exception(f"error: cannot get target disk from {RHEL_VM_NAME} with command [lsblk]")

    Case.step(f'Launch {RHEL_VM_NAME}')
    kvm.start_vm(RHEL_VM_NAME)

    Case.step(f'Install fio in {RHEL_VM_NAME}')
    cmd_install_fio = f'yum install -y fio'
    kvm.execute_vm_cmd(RHEL_VM_NAME, cmd_install_fio)

    Case.step(f'Run fio test in {RHEL_VM_NAME}')
    cmd_run_fio = f'fio -filename=/dev/{last_disk_name} -direct=1 -iodepth 1 -thread -rw=randread -ioengine=psync -bs=4k' +\
                  ' -size=5G -numjobs=50 -runtime=180 -group_reporting -name=rand_100read_4k'
    rcode, _, std_err = kvm.execute_vm_cmd(RHEL_VM_NAME, cmd_run_fio, timeout=200)
    if rcode != 0:
        raise Exception(std_err)

    Case.step("Restore environment")
    kvm.shutdown_vm(RHEL_VM_NAME)


def clean_up(sut):
    if Result.returncode != 0 and Case.step_count < 1:
        cleanup.to_s5(sut)
    if Result.returncode != 0:
        kvm = get_vmmanger(sut)
        kvm.shutdown_vm(RHEL_VM_NAME)

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
