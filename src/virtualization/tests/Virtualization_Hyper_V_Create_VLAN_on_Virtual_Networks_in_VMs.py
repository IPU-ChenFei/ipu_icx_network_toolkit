"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509888801
 @Author: Han, Yufeng
 @Prerequisite:
    1. HW Configuration
        Plug 1 MLX NIC on SUT
    2. SW Configuration
        1. Install a windows virtual machine named "windows1"
        2. copy "\\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\\auto-poc.zip" to
           "C:\\BKCPkg\\domains\\virtualization" and unzip it
        3. Install updated pip and paramiko
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    '1. BIOS SettingEDKII Menu -- Socket Configuration -- Processor Configuration -- VMX -> Enable'
    'EDKII Menu -- Socket Configuration -- IIO Configuration - VTd -> Enable'
    'EDKII Menu -- Platform Configuration -- Miscellaneous Configuration -- SR-IOV Support -> Enable'
    '2. Connect an external Mellanox Ethernet Adapter that supports SR-IOV to SUT'
    '3. Driver Installation'
    'Latest Driver for the PCIe device installed on both SUT and the VM image'
    'Check vendor website for the latest driver.https://www.mellanox.com/products/adapter-software/ethernet/windows/winof-2'
    'For ConnectX-3 and ConnectX-3 Pro drivers download WinOF.For ConnectX-4 and onwards adapter cards drivers download WinOF-2.'
    '4. Install Hyper-V (Refer to \'Virtualization - Hyper-V - Install Hypervisor\')'
    '5. Create a VM with the vhdx disk file that contains the correct setup, such as OS, driver, etc.'
    'Create windows VM (Refer to \'Virtualization - Hyper-V - Guest OS Install & Config\')'
    '6. OnSUT, enable the IovEnableOverride Field in the Windows Registry:'
    'Open regedit.exe and browse to the following location: Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\WindowsNT\CurrentVersion\Virtualization'
    'Insert a registry key of type DWORD (32-bit): IovEnableOverride'
    'Set the value of that key to 1'
]


def get_interface_blks(sut):
    # type: (SUT) -> [str]
    _, out, _ = sut.execute_shell_cmd("Get-NetIPConfiguration", powershell=True)
    temp = out.split("\n\n")
    blocks = []
    for blk in temp:
        if blk != "":
            blocks.append(blk)
    return blocks


def get_nic_ip(sut, keyword):
    blocks = get_interface_blks(sut)

    target_blk = ""
    for blk in blocks:
        if keyword in blk:
            target_blk = blk
    if target_blk == "":
        raise Exception(f"error: cannot find interface with keyword {keyword}")

    blk_lines = target_blk.splitlines()
    for line in blk_lines:
        if "IPv4Address" in line:
            return line.split(":")[-1]


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    sut1 = sut
    sut2 = get_sut_list()[1]
    hyperv1 = get_vmmanger(sut1)
    hyperv2 = get_vmmanger(sut2)

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut1, 'windows1'))
    Case.precondition(FilePrecondition(sut1, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.precondition(NicPrecondition(sut1, 'MLX NIC', 'Mell'))
    Case.precondition(VirtualMachinePrecondition(sut2, 'windows1'))
    Case.precondition(FilePrecondition(sut2, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.precondition(NicPrecondition(sut2, 'MLX NIC', 'Mell'))
    Case.check_preconditions()

    # SUT1:
    Case.step('SUT1 Enable SR-IOV')
    cmd = f"Get-VMNetworkAdapter -ManagementOs -Name \'{MELL_NIC_SWITCH_NAME}\'"
    VIanID1 = f'{cmd} | Set-VMNetworkAdapterVlan -Access -VlanID 1'
    VIanID2 = f'{cmd} | Set-VMNetworkAdapterVlan -Access -VlanID 2'
    MELL_NIC = hyperv1.get_netadapter_by_keyword(MELL_NIC_NAME)[0]
    hyperv1.create_switch(MELL_NIC_SWITCH_NAME, False, MELL_NIC)
    code, out, err = sut1.execute_shell_cmd(VIanID2, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    # SUT2:
    Case.step('SUT2 Enable SR-IOV')
    MELL_NIC = hyperv2.get_netadapter_by_keyword(MELL_NIC_NAME)[0]
    hyperv2.create_switch(MELL_NIC_SWITCH_NAME, False, MELL_NIC)
    code, out, err = sut2.execute_shell_cmd(VIanID2, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    Case.step('get SUT1 IP')
    SUT1_IP = get_nic_ip(sut1, MELL_NIC_SWITCH_NAME)

    Case.step('get SUT2 IP')
    SUT2_IP = get_nic_ip(sut2, MELL_NIC_SWITCH_NAME)

    Case.step('ping SUT1/SUT2 IP fine')
    _, std_out1, _ = sut1.execute_shell_cmd(f'ping /n 2 {SUT2_IP}', timeout=30, powershell=True)
    Case.expect('SUT2 ping SUT1 fine', '0% loss' in std_out1)
    _, std_out2, _ = sut2.execute_shell_cmd(f'ping /n 2 {SUT1_IP}', timeout=30, powershell=True)
    Case.expect('SUT2 ping SUT1 fine', '0% loss' in std_out2)

    Case.step('SUT1 change the VLAN ID to 1')
    code, out, err = sut1.execute_shell_cmd(VIanID1, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    Case.step('ping SUT1/SUT2 IP error')
    _, std_out1, _ = sut1.execute_shell_cmd(f'ping /n 2 {SUT2_IP}', timeout=30, powershell=True)
    Case.expect('SUT2 ping SUT1 error', '100% loss' in std_out1 or "Destination host unreachable" in std_out1)
    _, std_out2, _ = sut2.execute_shell_cmd(f'ping /n 2 {SUT1_IP}', timeout=30, powershell=True)
    Case.expect('SUT2 ping SUT1 error', '100% loss' in std_out2 or "Destination host unreachable" in std_out2)

    Case.step('ADD mellanox to vm')
    hyperv1.attach_nic_to_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv2.attach_nic_to_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    VIanID1_VM = f'Set-VMNetworkAdapterVlan -VMNetworkAdapterName {MELL_NIC_SWITCH_NAME} -VMName {WINDOWS_VM_NAME} -Access -VlanId 1'
    VIanID2_VM = f'Set-VMNetworkAdapterVlan -VMNetworkAdapterName {MELL_NIC_SWITCH_NAME} -VMName {WINDOWS_VM_NAME} -Access -VlanId 2'

    Case.step('SUT1_VM change the VLAN ID to 2')
    code, out, err = sut1.execute_shell_cmd(VIanID2, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)
    code, out, err = sut1.execute_shell_cmd(VIanID2_VM, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    Case.step('SUT2_VM change the VLAN ID to 2')
    code, out, err = sut2.execute_shell_cmd(VIanID2, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)
    code, out, err = sut2.execute_shell_cmd(VIanID2_VM, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    Case.step('SUT1_VM/SUT2_VM ping ok')
    hyperv1.start_vm(WINDOWS_VM_NAME)
    hyperv2.start_vm(WINDOWS_VM_NAME)
    out1 = hyperv1.get_vm_ip(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    out2 = hyperv2.get_vm_ip(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    _, std_out1, _ = hyperv1.execute_vm_cmd(WINDOWS_VM_NAME, f'ping /n 2 {out2}', timeout=30, powershell=True)
    Case.expect('SUT1_VM ping SUT2_VM fine', '0% loss' in std_out1)
    _, std_out2, _ = hyperv2.execute_vm_cmd(WINDOWS_VM_NAME, f'ping /n 2 {out1}', timeout=60, powershell=True)
    Case.expect('SUT2_VM ping SUT1_VM fine', '0% loss' in std_out2)
    hyperv1.shutdown_vm(WINDOWS_VM_NAME)
    hyperv2.shutdown_vm(WINDOWS_VM_NAME)

    Case.step('SUT1_VM change the VLAN ID to 1')
    code, out, err = sut1.execute_shell_cmd(VIanID1, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)
    code, out, err = sut1.execute_shell_cmd(VIanID1_VM, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    Case.step('SUT1_VM/SUT2_VM ping error')
    hyperv1.start_vm(WINDOWS_VM_NAME)
    hyperv2.start_vm(WINDOWS_VM_NAME)
    _, std_out1, _ = hyperv1.execute_vm_cmd(WINDOWS_VM_NAME, f'ping /n 2 {out2}', timeout=30, powershell=True)
    Case.expect('SUT1_VM ping SUT2_VM error', '100% loss' in std_out1 or "Destination host unreachable" in std_out1)
    _, std_out2, _ = hyperv2.execute_vm_cmd(WINDOWS_VM_NAME, f'ping /n 2 {out1}', timeout=30, powershell=True)
    Case.expect('SUT2_VM ping SUT1_VM error', '100% loss' in std_out2 or "Destination host unreachable" in std_out2)

    Case.step('Shutdown VM and remove VM switch network adapter')
    hyperv1.shutdown_vm(WINDOWS_VM_NAME, 600)
    hyperv1.detach_nic_from_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv1.delete_switch(MELL_NIC_SWITCH_NAME)
    hyperv2.shutdown_vm(WINDOWS_VM_NAME, 600)
    hyperv2.detach_nic_from_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv2.delete_switch(MELL_NIC_SWITCH_NAME)


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
