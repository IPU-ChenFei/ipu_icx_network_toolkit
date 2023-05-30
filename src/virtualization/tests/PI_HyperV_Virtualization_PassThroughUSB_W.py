"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883639
 @Author: Han, Yufeng
 @Prerequisite:
    1. HW Configuration
        Plug 1 Mobile HD on SUT
    2. SW Configuration
        1. Install a windows virtual machine named "windows1"
        2. copy "\\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\\auto-poc.zip" to
           "C:\\BKCPkg\\domains\\virtualization" and unzip it
        3. Install updated pip and paramiko
"""

from src.virtualization.lib.tkinit import *

CASE_DESC = [
    # TODO
    'it\'s a case template',
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


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
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.check_preconditions()

    # Step 1
    Case.step('Reset the USB hard drive to offline and attach it to virtual machine')
    hyperv = get_vmmanger(sut)
    usb_disk_keyword = ParameterParser.parse_parameter("usb")
    if usb_disk_keyword == "":
        raise Exception("Input the keyword of USB by --usb=xxx please")
    usb_id = hyperv.get_disk_id_by_keyword(usb_disk_keyword)[0]
    cmd = get_reset_disk_cmd(sut, usb_id)
    sut.execute_shell_cmd(cmd, powershell=True)
    cmd = f"set-disk -number {usb_id} -isoffline $true"
    sut.execute_shell_cmd(cmd, powershell=True)
    hyperv.attach_physical_disk_to_vm(WINDOWS_VM_NAME, usb_id)

    # Step2
    Case.step('Start virtual machine')
    hyperv.start_vm(WINDOWS_VM_NAME)

    # Step 4
    Case.step('Set disk attribute in VM')
    cmd = 'Set-Disk -Number 1 -IsReadonly $false; '
    cmd += 'set-disk -number 1 -isoffline $false'
    code, out, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, cmd, timeout=600, powershell=True)
    Case.expect('return code == 0 and no error info', code == 0 and len(stderr.strip()) == 0)

    #  Step 5
    Case.step('test basic functionality of USB hard drive')
    cmd = r'$drives = [Environment]::GetLogicalDrives(); '
    cmd += r'echo 1 > C:\\tmp.log; '
    cmd += r'copy C:\tmp.log $drives[-1]; '
    cmd += r'ls $drives[-1]; '
    code, out, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, cmd, timeout=60, powershell=True)
    Case.expect('return code == 0 and no error info', code == 0 and len(stderr.strip()) == 0)

    # Step 6
    Case.step('Restore the environment')
    Case.sleep(60)
    hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
    hyperv.detach_physical_disk_from_vm(WINDOWS_VM_NAME, usb_id)


def clean_up(sut):
    if Result.returncode != 0:
        if Case.step_count < 1:
            cleanup.to_s5(sut)
        if Case.step_count >= 1:
            hyperv = get_vmmanger(sut)
            usb_disk_keyword = ParameterParser.parse_parameter("usb")
            if usb_disk_keyword == "":
                raise Exception("Input the keyword of USB by --usb=xxx please")
            usb_id = hyperv.get_disk_id_by_keyword(usb_disk_keyword)[0]
            hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
            hyperv.detach_physical_disk_from_vm(WINDOWS_VM_NAME, usb_id)


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