"""
 @Case Link:https://hsdes.intel.com/appstore/article/#/1509883810
 @Author:YanXu
 @Prerequisite:
    1. HW Configuration
        1. USB
    2. SW Configuration
        1. SUT Python package
        2. Tools
        3. Files
    3. Virtual Machine
        1. Create a centos VM
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Configure USB Storage pass-through devices on an ESXi host Procedures"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.check_preconditions()

    esxi = get_vmmanger(sut)
    vmfs_pass = f'/vmfs/volumes/datastore1/{RHEL_VM_NAME}/{RHEL_VM_NAME}.vmx'

    esxi.shutdown_vm(RHEL_VM_NAME)
    Case.step('add 3.0 USB control through the command')
    esxi.execute_host_cmd_esxi(f"$vmname = '{RHEL_VM_NAME}';" +
                               "$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;" +
                               "$deviceCfg = New-Object VMware.Vim.VirtualDeviceConfigSpec;" +
                               "$deviceCfg.Operation = 'add';" +
                               "$deviceCfg.Device = New-Object VMware.Vim.VirtualUSBXHCIController;" +
                               "$deviceCfg.Device.Key = -1;" +
                               "$deviceCfg.Device.Connectable = New-Object VMware.Vim.VirtualDeviceConnectInfo;" +
                               "$deviceCfg.Device.Connectable.StartConnected - $true -1;" +
                               "$deviceCfg.Device.Connectable.AllowGuestControl = $true;" +
                               "$deviceCfg.Device.Connectable.Connected = $true;" +
                               "$deviceCfg.Device.ControllerKey = 100;" +
                               "$deviceCfg.Device.BusNumber = -1;" +
                               "$deviceCfg.Device.autoConnectDevices = $true;" +
                               "$spec.DeviceChange += $deviceCfg;" +
                               "$vm = Get-VM -Name $vmname | Get-View;" +
                               "$vm.ReconfigVM_Task($spec)")

    Case.step('Use command to check usb PID_Number and VID_Number')
    _, usb, _ = sut.execute_shell_cmd(f'lsusb | grep -i {USB_TYPE}')
    usb = log_check.find_lines(USB_TYPE, usb)[0]
    str_split = usb.split(" ")
    id = str_split[5]
    pid = '0x' + id[0:5] + '0x' + id[5:]

    Case.step('Add the following fields under the <RHEL_VM_NAME>.vmx file of VM')
    sut.execute_shell_cmd(f'echo usb.autoConnect.device0 = "{pid}" >> {vmfs_pass}')

    Case.step('Start VM')
    esxi.start_vm(RHEL_VM_NAME, timeout=120)

    Case.step('Get VM ip')
    esxi.get_vm_ip(RHEL_VM_NAME)

    Case.step('Enter the command to view the USB device')
    _, usb_dev, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, "df -h | grep media")
    Case.expect('The USB attached successfully', usb_dev.strip() != "")

    Case.step('Mount the USB flash drive to / mnt/usb')
    esxi.execute_vm_cmd(RHEL_VM_NAME, 'mkdir /mnt/usb')
    dev_name = usb_dev.split()[0]
    esxi.execute_vm_cmd(RHEL_VM_NAME, f'mount {dev_name} /mnt/usb/', cwd='/mnt')

    Case.step('Write data to USB flash disk and check whether it has been written successfully:')
    esxi.execute_vm_cmd(RHEL_VM_NAME, 'echo 1111 > /mnt/usb/2.txt')
    _, result, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, 'cat /mnt/usb/2.txt')
    Case.expect('The file can be created and saved successfully', "1111" in result)

    Case.step('Copy the files in the USB flash disk to the VM and check whether the data is correct')
    esxi.execute_vm_cmd(RHEL_VM_NAME, 'cp /mnt/usb/2.txt ~')
    _, result, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, 'cat ~/2.txt')
    Case.expect('The documents entered can be output correctly', '1111' in result)

    esxi.execute_vm_cmd(RHEL_VM_NAME, "rm -f /mnt/usb/2.txt")
    esxi.execute_vm_cmd(RHEL_VM_NAME, "rm -f ~/2.txt")
    esxi.execute_vm_cmd(RHEL_VM_NAME, f'umount {dev_name}', cwd='/mnt')
    esxi.shutdown_vm(RHEL_VM_NAME)
    sut.execute_shell_cmd(f"sed -i '/^usb.autoConnect.device0/d' {vmfs_pass}")


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