"""
@Case Link: https://hsdes.intel.com/appstore/article/#/1509884267
@Author:Liu, JianjunX
@Prerequisite:
1. HW Configuration
    2. Plug a PCIe Storage device into SUT
2. SW Configuration
    1. Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
    2.  Create two windows VMs
        Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Windows) Installation'
    3.  Passthrough a VF of NIC to two Windows VM, respectively.
        Refer to 'PI_Virtualization_SR-IOVBasicCheck_V'
    4. Tools
         ntttcp.zip
          ethr_windows.zip
    5. Files
    6. virtual machine
            linux_vm_name = 'rhel1'

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Purpose of this test case is to stress the VMware esxi OS using ethr and nttcp tools."
]


def enable_SRIOV(esxi, dev_id, server_ip, num=1):
    cmd = '$spec=New-Object VMware.Vim.HostSriovConfig;' \
          '$spec.SriovEnabled="$true";' \
          f'$spec.NumVirtualFunction="{num}";' \
          f'$spec.Id=\\"{dev_id}\\";' \
          f'$spec.ApplyNow="$true";' \
          f'$esx=Get-VMHost {server_ip};' \
          f'$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;' \
          f'$ptMgr.UpdatePassthruConfig($spec);echo $spec'
    rcode, std_out, std_err = esxi.execute_host_cmd_esxi(cmd, timeout=60 * 2)
    return rcode, std_out, std_err


def get_dhcp_pf_ids(esxi, nics):
    """
    Get the IDS of the specified network card type and connect the network cable
    return: list
    """
    pci_ids = []
    pf_ids = []
    code, out, err = esxi.execute_host_cmd_esxi(
        "Get-VMHostNetworkAdapter -Physical| Where-Object {$_.FullDuplex -match 'True'} | fl")
    out = log_check.find_lines("PciId              :", out)
    for id in out:
        temp = id.replace("PciId              : ", "")
        pci_ids.append(temp)
    nics = str(nics)[:-1].split('\n')
    for nic in nics:
        nic = nic.strip().split(' ')[0]
        if any(nic in s for s in pci_ids):
            pf_ids.append(nic)
    return pf_ids


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to uefi shell")
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.precondition(VirtualMachinePrecondition(sut, 'windows2'))
    Case.precondition(DiskPrecondition(sut, 'NVME SSD', 'NVM'))
    Case.check_preconditions()

    port = 10000
    ethr_run_time = '1m'
    ntttcp_run_time = 30

    server_ip = sut.supported_os[sut.default_os].ip
    Case.step("Connect to server: ")
    esxi = get_vmmanger(sut)
    esxi.shutdown_vm(WINDOWS_VM_NAME)
    esxi.shutdown_vm(WINDOWS_VM_NAME2)

    Case.step('Passthrough a VF of NIC to two Windows VM, ')
    _, nics, err = sut.execute_shell_cmd(f"lspci | grep {X710_NIC_TYPE}")
    pf_ids = get_dhcp_pf_ids(esxi, nics)
    Case.expect("get NIC success", len(pf_ids) >= 1)

    PF_ID1 = pf_ids[0]
    rcode, std_out, std_err = enable_SRIOV(esxi, PF_ID1, server_ip, 2)
    Case.expect(f"Enable SRIOV {PF_ID1}", std_err is None)
    #
    code, out, err = esxi.execute_host_cmd_esxi(f'$nic = Get-NetworkAdapter -VM {WINDOWS_VM_NAME};'
                                                r'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false')
    Case.expect(f"add sriov vm1 {WINDOWS_VM_NAME} success", err is None)
    code, out, err = esxi.execute_host_cmd_esxi(f'$nic = Get-NetworkAdapter -VM {WINDOWS_VM_NAME2};'
                                                r'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false')
    Case.expect(f"add sriov vm2 {WINDOWS_VM_NAME2} success", err is None)

    Case.step(f"Add a new SR-IOV network adapter: {WINDOWS_VM_NAME}")
    code, out, err = esxi.execute_host_cmd_esxi(
        f"New-NetworkAdapter -VM {WINDOWS_VM_NAME} -type SriovEthernetCard -NetworkName 'VM Network' -PhysicalFunction '{PF_ID1}'")
    Case.expect("Add SR-IOV network adapter success", err is None)

    Case.step(f"Add a new SR-IOV network adapter: {WINDOWS_VM_NAME2}")
    code, out, err = esxi.execute_host_cmd_esxi(
        f"New-NetworkAdapter -VM {WINDOWS_VM_NAME2} -type SriovEthernetCard -NetworkName 'VM Network' -PhysicalFunction '{PF_ID1}'")
    Case.expect("Add SR-IOV network adapter success", err is None)

    Case.step( '"Reserve all guest memory"(All Locked), use the command below to select:')
    _, out, err = esxi.execute_host_cmd_esxi("$spec=New-Object VMware.Vim.VirtualMachineConfigSpec;"
                                             "$spec.memoryReservationLockedToMax = $true;"
                                             f"(Get-VM {WINDOWS_VM_NAME}).ExtensionData.ReconfigVM_Task($spec)")
    Case.expect("setting Reserve all guest memory successful!", err is None)
    Case.step('"Reserve all guest memory"(All Locked), use the command below to select:')
    _, out, err = esxi.execute_host_cmd_esxi("$spec=New-Object VMware.Vim.VirtualMachineConfigSpec;"
                                             "$spec.memoryReservationLockedToMax = $true;"
                                             f"(Get-VM {WINDOWS_VM_NAME2}).ExtensionData.ReconfigVM_Task($spec)")
    Case.expect("setting Reserve all guest memory successful!", err is None)

    esxi.start_vm(WINDOWS_VM_NAME)
    esxi.start_vm(WINDOWS_VM_NAME2)

    Case.step("SSH connect to VM1 and VM2, respectively:")
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, 'ipconfig')
    win1_ip = esxi.get_vm_ip(WINDOWS_VM_NAME)
    Case.expect(f"SSH connect {WINDOWS_VM_NAME} success", std_err == "" and len(win1_ip) != 0)
    win2_ip = esxi.get_vm_ip(WINDOWS_VM_NAME2)
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME2, 'ipconfig')
    Case.expect(f"SSH connect {WINDOWS_VM_NAME2} success", std_err == "" and len(win2_ip) != 0)

    Case.step("Set the input and output ports of firewall of VM1 and VM2, respectively:")
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME,
                                                  'netsh advfirewall firewall add rule name="TCP Port any " dir=in '
                                                  'action=allow protocol=TCP localport=any')
    Case.expect(f"Set the input and output ports of firewall of {WINDOWS_VM_NAME} success", std_err == "")
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME,
                                                  'netsh advfirewall firewall add rule name="TCP Port any " dir=in '
                                                  'action=allow protocol=TCP localport=any')
    Case.expect(f"Set the input and output ports of firewall of {WINDOWS_VM_NAME2} success", std_err == "")

    Case.step(f"Run ethr on Server Mode on VM1 {WINDOWS_VM_NAME} SSH connection :")
    win_ip1 = esxi.get_vm_ip(WINDOWS_VM_NAME)

    t_s = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
    s_result_log = f'ethrs-{t_s}.log'
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME,
                                                  f"start cmd /K {ETHR_TOOL_PATH}\\ethr.exe -s -port {port}"
                                                  f" -o {ETHR_TOOL_PATH}\\{s_result_log} & exit")
    Case.expect(f"Run ethr on Server Mode on VM1 {WINDOWS_VM_NAME} success", std_err == "")
    Case.sleep(60)
    Case.step(f"Run ethr on Client Mode on VM2 {WINDOWS_VM_NAME2} SSH connection:")
    c_result_log = f'ethrc-{t_s}.log'

    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME2, f'{ETHR_TOOL_PATH}\\ethr.exe -c {win_ip1} '
                                                             f'-l 1KB -n 1024 -port {port} -d {ethr_run_time} '
                                                             f'-o {ETHR_TOOL_PATH}\\{c_result_log}',
                                                  timeout=60 * 60 * 48)
    Case.expect(f"Run ethr on Server Mode on VM2 {WINDOWS_VM_NAME2} success", rcode == 0)

    os.mkdir(os.path.join(LOG_PATH, 'result'))
    result = f"{os.path.join(LOG_PATH, 'result')}\\{s_result_log}"
    esxi.download_from_vm(WINDOWS_VM_NAME, result, f"{ETHR_TOOL_PATH}\\{s_result_log}")
    result = f"{os.path.join(LOG_PATH, 'result')}\\{c_result_log}"
    esxi.download_from_vm(WINDOWS_VM_NAME2, result, f"{ETHR_TOOL_PATH}\\{c_result_log}")

    Case.step(f"Run NTttcp on Receiver Mode on VM1 {WINDOWS_VM_NAME} SSH connection:")
    t_s = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
    n_r_result_log = f'NTttcp_r-{t_s}.log'
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME,
                                                  f"start cmd /K {NTTTCP_TOOL_PATH}\\Ntttcp.exe -r -m "
                                                  f"1,0,{win_ip1} 1,1,{win_ip1} -t {ntttcp_run_time} -l 1K -p 55000 "
                                                  f"-xml {NTTTCP_TOOL_PATH}\\{n_r_result_log} & exit")
    Case.expect("Run NTttcp on Receiver Mode success", rcode == 0)

    Case.step(f"Run NTttcp on Sender Mode on VM2 {WINDOWS_VM_NAME2} SSH connection with the same parameters:")
    n_s_result_log = f'NTttcp_s-{t_s}.log'
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME2,
                                                  f"{NTTTCP_TOOL_PATH}\\Ntttcp.exe -s -m "
                                                  f"1,0,{win_ip1} 1,1,{win_ip1} -t {ntttcp_run_time} -l 1K -p 55000 "
                                                  f"-xml {NTTTCP_TOOL_PATH}\\{n_s_result_log}",
                                                  timeout=ntttcp_run_time + 60 * 2)
    Case.expect("Run NTttcp on Sender Mode success", std_err == "")

    Case.step("SSH connect to VM1 and VM2, respectively:")
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, 'ipconfig')
    Case.expect(f"SSH connect {WINDOWS_VM_NAME} success", std_err == "")
    rcode, std_out, std_err = esxi.execute_vm_cmd(WINDOWS_VM_NAME2, 'ipconfig')
    Case.expect(f"SSH connect {WINDOWS_VM_NAME2} success", std_err == "")
    Case.sleep(60)
    r_result = f"{os.path.join(LOG_PATH, 'result')}\\{n_r_result_log}"
    esxi.download_from_vm(WINDOWS_VM_NAME, r_result, f"{NTTTCP_TOOL_PATH}\\{n_r_result_log}")
    s_result = f"{os.path.join(LOG_PATH, 'result')}\\{n_s_result_log}"
    esxi.download_from_vm(WINDOWS_VM_NAME2, s_result, f"{NTTTCP_TOOL_PATH}\\{n_s_result_log}")

    # remove
    Case.step("restore vm env")
    esxi.shutdown_vm(WINDOWS_VM_NAME)
    esxi.shutdown_vm(WINDOWS_VM_NAME2)
    esxi.execute_host_cmd_esxi(f'$nic = Get-NetworkAdapter -VM {WINDOWS_VM_NAME} |'
                               r' Where-Object{$_.Name -match \"SR-IOV\"};'
                               r'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false')
    esxi.execute_host_cmd_esxi(f"New-NetworkAdapter -VM {WINDOWS_VM_NAME} -NetworkName 'VM Network' -StartConnected")
    esxi.execute_host_cmd_esxi(f'$nic = Get-NetworkAdapter -VM {WINDOWS_VM_NAME2} |'
                               r' Where-Object{$_.Name -match \"SR-IOV\"};'
                               r'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false')
    esxi.execute_host_cmd_esxi(f"New-NetworkAdapter -VM {WINDOWS_VM_NAME2} -NetworkName 'VM Network' -StartConnected")


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
