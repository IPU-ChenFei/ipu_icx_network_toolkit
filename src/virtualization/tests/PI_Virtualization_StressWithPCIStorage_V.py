"""
@Case Link: https://hsdes.intel.com/appstore/article/#/1509883771
@Author:Liu, JianjunX
@Prerequisite:
1. HW Configuration
    1. Plug a PCIe Storage device into SUT
2. SW Configuration
    1. Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
        copy folder iometer-1.1.0-win64.x86_64-bin tool
    2.  Set up a Centos VM
        install iometer and disable firewall with the following commands:
        systemctl disable firewalld
        systemctl stop firewalld
    3.  Download IOmeter to external Windows host
    2. Tools
        iometer-1.1.0-win64.x86_64-bin.zip
        C:\\BKCPkg\\domains\\virtualization\\tools
    3. Files
    4. virtual machine
        linux_vm_name = 'rhel1'
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Verify SRIOV VF adapter can be generated for working'
]


def csv_file_analysis(file, key):
    df = pd.DataFrame(pd.read_csv(file, encoding='utf-8', skiprows=13, usecols=[key]))
    result = df[key].value_counts()
    res = dict(result)
    flag = False
    if len(res) == 1 and 0 in res.keys():
        flag = True
    if len(res) == 2 and 0 in res.keys() and key in res.keys():
        flag = True
    return flag, result


def restore_vm(esxi, vm_name):
    Case.step("restore vm env")
    esxi.shutdown_vm(vm_name)
    _, out, err = esxi.execute_host_cmd_esxi(
        f'Get-PassthroughDevice -VM {vm_name} | Remove-PassthroughDevice -confirm:$false')
    Case.expect("restore vm successful ", err is None)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to uefi shell")
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(DiskPrecondition(sut, 'NVME SSD', 'NVM'))
    Case.precondition(HostFilePrecondition(sut, 'iometer/', sut_tool('VT_IOMETER_H')))
    Case.check_preconditions()

    server_ip = sut.supported_os[sut.default_os].ip
    Case.step('Connect to server:')
    esxi = get_vmmanger(sut)
    Case.step('Make the PCIe disk ready for passthrough.')
    code, devs, err = sut.execute_shell_cmd(f"lspci | grep -i {PCI_NVM_TYPE}")
    Case.expect(f"pci NVME SSD output results:[{devs}]", devs != "")
    Case.step("Active the PCI device:")
    dev_id = log_check.scan_format("%s ", devs)[0]
    code, out, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={dev_id} -e=on  -a")
    Case.expect("The device is configured to passthru.", err == "")

    Case.step("Assign the PCIe disk to VM.")
    restore_vm(esxi, RHEL_VM_NAME)
    code, out, err = esxi.execute_host_cmd_esxi(f'$devs=Get-PassthroughDevice -VMHost {server_ip} | '
                                                f'Where-Object {{$_.Uid -like \\"*{dev_id}*\\"}};'
                                                f'Add-PassthroughDevice -VM {RHEL_VM_NAME} -PassthroughDevice $devs[0]')
    Case.expect("add PassthroughDevice success", err is None)
    esxi.start_vm(RHEL_VM_NAME)
    code, out, err = esxi.execute_vm_cmd(RHEL_VM_NAME, f"lspci | grep -i {PCI_NVM_TYPE}")
    Case.expect("NVMe disk is present in VM", out != "")

    Case.step("Run IOmeter inside VM for a few hours and confirm no error.")
    code, out, err = sut.execute_host_cmd("ipconfig")
    out = log_check.find_lines(server_ip[0:5], out)[0]
    win_ip = log_check.scan_format("IPv4 Address. . . . . . . . . . . : %s", out)[0]
    lin_ip = esxi.get_vm_ip(RHEL_VM_NAME).strip()
    rcode, std_out, std_err = esxi.execute_vm_cmd(RHEL_VM_NAME, f"chmod +777 {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/dynamo")
    Case.expect("chmod successful", std_err == "")

    cmd = f"{sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/dynamo -i {win_ip} -m {lin_ip} -n {RHEL_VM_NAME} "
    esxi.execute_vm_cmd(RHEL_VM_NAME, f'{cmd} &')
    log_path = f"{LOG_PATH}\\results"
    os.mkdir(log_path)
    res_log = f"{log_path}\\results.csv"
    sut.execute_host_cmd(f"IOmeter.exe /c nvme.icf /r {res_log}",
                         cwd=HOST_IOMETER_PATH, timeout=60 * 60 * 3)
    flag, result = csv_file_analysis(res_log, "Packet Errors")
    Case.expect(f"Iometer run pass! \r\n{result}\r\n", flag)
    restore_vm(esxi, RHEL_VM_NAME)
    code, out, err = sut.execute_shell_cmd(f"esxcli hardware pci pcipassthru set -d={dev_id} -e=off  -a")
    Case.expect("The device is configured to passthru.", err == "")
    sut.execute_shell_cmd('reboot')
    Case.sleep(60*3)
    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)


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
