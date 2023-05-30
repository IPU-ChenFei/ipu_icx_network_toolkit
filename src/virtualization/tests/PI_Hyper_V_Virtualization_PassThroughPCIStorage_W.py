"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509876327
 @Author: Han, Yufeng
 @Prerequisite:
    1. HW Configuration
        Plug 1 HD on SUT
    2. SW Configuration
        1. Install 2 windows virtual machine named "windows1", "windows2"
        2. copy "\\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\\auto-poc.zip" to
           "C:\\BKCPkg\\domains\\virtualization" and unzip it
        3. Install updated pip and paramiko
"""

from src.virtualization.lib.tkinit import *

CASE_DESC = [
    # TODO
    " 1. BIOS Setting "
    " EDKII Menu -- Socket Configuration -- Processor Configuration -- VMX -> Enable"
    " EDKII Menu -- Socket Configuration -- IIO Configuration -- VTd -> Enable"
    " 2. Install Hyper-V (Refer to 'Virtualization - Hyper-V - Install Hypervisor')"
    " 3. Create windows VM (Refer to 'Virtualization - Hyper-V - Guest OS Install & Config')"
    " 4. Connect two PCIe storage disks to SUT,  make sure PCIe storage disks are detected by SUT OS"
]


def get_nvme_disk_id_list(sut):
    cmd = f"wmic diskdrive get /value | findstr PNPDeviceID"
    dev_id_list = sut.execute_shell_cmd(cmd)[1].splitlines()
    cmd = f"wmic diskdrive get /value | findstr Partitions"
    partition_list = sut.execute_shell_cmd(cmd)[1].splitlines()
    cmd = f"wmic diskdrive get /value | findstr Index"
    id_list = sut.execute_shell_cmd(cmd)[1].splitlines()

    disk_list = []
    for i in range(len(dev_id_list)):
        if "NVM" in dev_id_list[i] and int(partition_list[i].strip().split("=")[-1]) < 3:
            disk_list.append(id_list[i].strip().split("=")[-1])

    return disk_list


def get_reset_disk_cmd(sut, disk_id):
    hyperv = get_vmmanger(sut)
    _, out, _ = sut.execute_shell_cmd(f"wmic diskdrive get /value", powershell=True)
    blocks = hyperv.get_disk_info_blocks(out)

    for blk in blocks:
        if int(blk["Index"].strip()) == int(disk_id):
            friendly_name = blk["Model"].strip()

    cmd = f"set-disk -Num {disk_id} -IsOffline $false; "
    cmd += f"Clear-Disk -Number {disk_id} -RemoveData -RemoveOEM -confirm:$false; "
    cmd += f"$new_disk=Get-Disk | Where-Object {{$_.Number -match {disk_id}}}; "
    cmd += f"$new_disk | New-Volume -FileSystem NTFS -FriendlyName \"{friendly_name}\""
    return cmd


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # Prepare steps - Enable VTD and VMX in BIOS
    Case.prepare("boot to Windows")
    boot_to_with_bios_knobs(sut, sut.default_os, 'VTdSupport', '0x1', "ProcessorVmxEnable", "0x1")

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1', True))
    Case.precondition(VirtualMachinePrecondition(sut, 'windows2', True))
    Case.precondition(DevicePrecondtion(sut, 'NVME SSD'))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.check_preconditions()

    hyperv = get_vmmanger(sut)
    # nvme_disk_keyword = ParameterParser.parse_parameter("nvme")
    # if nvme_disk_keyword == "":
    #     raise Exception("Input the keyword of USB by --nvme=xxx please")
    nvme_disk_id_list = get_nvme_disk_id_list(sut)
    vm_name_list = [WINDOWS_VM_NAME, WINDOWS_VM_NAME2]
    for i in range(2):
        Case.step(f'Reset the {i}th PCIe Disk drive to offline and attach it to {vm_name_list[i]}')
        # used_nvme_ssd_id = hyperv.get_disk_id_by_keyword(nvme_disk_keyword)[i]
        used_nvme_ssd_id = nvme_disk_id_list[i]
        cmd = get_reset_disk_cmd(sut, used_nvme_ssd_id)
        sut.execute_shell_cmd(cmd, powershell=True)
        cmd = f"set-disk -number {used_nvme_ssd_id} -isoffline $true"
        sut.execute_shell_cmd(cmd, powershell=True)
        hyperv.attach_physical_disk_to_vm(vm_name_list[i], used_nvme_ssd_id)

        Case.step(f'Start vritual machine {vm_name_list[i]}')
        hyperv.start_vm(vm_name_list[i])

        Case.step('Set disk status')
        cmd = 'set-disk -number 1 -IsReadonly $false; '
        cmd += 'set-disk -number 1 -isoffline $false'
        (code, stdout, stderr) = hyperv.execute_vm_cmd(vm_name_list[i], cmd, timeout=600, powershell=True)
        Case.expect('return code == 0 and no error info', code == 0 and len(stderr.strip()) == 0)

        Case.step('test basic functionality of USB hard drive')
        cmd = r'$drives = [Environment]::GetLogicalDrives(); '
        cmd += r'echo 1 > C:\\tmp.log; '
        cmd += r'copy C:\\tmp.log $drives[-1]; '
        cmd += r'ls $drives[-1]; '
        code, out, stderr = hyperv.execute_vm_cmd(vm_name_list[i], cmd, timeout=60, powershell=True)
        Case.expect('return code == 0 and no error info', code == 0 and len(stderr.strip()) == 0)

        Case.step('Restore environment')
        hyperv.shutdown_vm(vm_name_list[i], 600)
        hyperv.detach_physical_disk_from_vm(vm_name_list[i], used_nvme_ssd_id)


def clean_up(sut):
    if Result.returncode != 0:
        hyperv = get_vmmanger(sut)
        nvme_disk_keyword = ParameterParser.parse_parameter("nvme")
        if nvme_disk_keyword == "":
            raise Exception("Input the keyword of USB by --nvme=xxx please")
        nvme_id1, nvme_id2 = hyperv.get_disk_id_by_keyword(nvme_disk_keyword)
        if Case.step_count < 1:
            cleanup.to_s5(sut)
        if 1 <= Case.step_count < 5:
            hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
            hyperv.detach_physical_disk_from_vm(WINDOWS_VM_NAME, nvme_id1)
        if 6 <= Case.step_count:
            hyperv.shutdown_vm(WINDOWS_VM_NAME2, 600)
            hyperv.detach_physical_disk_from_vm(WINDOWS_VM_NAME, nvme_id2)

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
