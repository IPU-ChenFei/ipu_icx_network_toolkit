"""
@Case Link: https://hsdes.intel.com/appstore/article/#/1509884225
@Author:Liu, JianjunX
@Prerequisite:
1. HW Configuration
    Plug two disks into SUT
2. SW Configuration
    1. Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
    2.  Create a centos VM
        Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Centos) Installation'
    3. create a vsphere
        Vsphere connected sut1
    4. Tools
        stressapptest-master.zip
    5. virtual machine
        linux_vm_name = 'rhel1'
3. case parameter example:
        eg:
            --sut=C:\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\configuration\config\sut\vsphere_sut.ini
            --sut=C:\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\configuration\config\sut\sut.ini

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Ensures that VMware's live storage migration feature functions w/o any issues or having to turn off the VM. "
    "This test case requires two hard drives to be available as this test case requires the tester to migrate a VM "
    "from one datastore to another. "
]


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
    Case.precondition(VirtualMachinePrecondition(sut, 'Vsphere'))
    Case.precondition(DiskPrecondition(sut, 'NVME SSD', 'NVM'))
    Case.check_preconditions()

    stressapptest_run_time = 10

    tool = "stressapptest-master"
    TOOL_PATH = f"{sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/{tool}"
    server_ip = sut.supported_os[sut.default_os].ip
    sut1 = sut
    sut2 = get_sut_list()[1]
    datastore_name = 'datastore2'
    Case.step("Connect to server: ")
    esxi = get_vmmanger(sut)
    esxi.start_vm(Vsphere)
    Case.sleep(60 * 10)
    #
    Case.step("Check the number of Datastore:")
    code, out, err = esxi.execute_host_cmd_esxi(f"Get-VMhost -Name {server_ip} |"
                                                f" Get-Datastore | "
                                                f"select DatastoreBrowserPath")
    Case.expect(f"get the output results success", err is None)
    Case.step("Check the list of Disks and Create another datastore:")
    if log_check.find_keyword(datastore_name, out) == "":
        code, out, err = esxi.execute_host_cmd_esxi(
            f"$disk=Get-VMHostDisk | Where-Object{{$_.DeviceName -match '{PCI_NVM_TYPE}'}};"
            f"foreach($i in $disk) {{if ($i.ExtensionData.Spec.Partition.Length -le 2 ){{$dev=$i;break;}}}};$dev")
        DeviceName = log_check.scan_format("DeviceName    :%s", out)
        Case.expect(f"create device name : {DeviceName[0]}", len(DeviceName) == 1)
        code, out, err = esxi.execute_host_cmd_esxi(
            f"$scsiLun = Get-ScsiLun -VMHost {server_ip} -LunType disk | "
            f"Where-Object{{$_.ConsoleDeviceName -match '{DeviceName[0]}'}};"
            f"$scsiLun;"
            f"New-Datastore -VMhost {server_ip} -Name {datastore_name} "
            f"-Path $scsiLun.canonicalName -Vmfs", timeout=60 * 3)
        Case.expect("The output results success ", err is None)

    Case.step("Check the number of Datastore again to comfirm the datastore has been already created:")
    code, out, err = esxi.execute_host_cmd_esxi(f"Get-VMhost -Name {server_ip} |"
                                                f" Get-Datastore | "
                                                f"select DatastoreBrowserPath")
    Case.expect("The output results success ", err is None)

    Case.step("Prepare for VM migration:")
    esxi.start_vm(RHEL_VM_NAME)

    Case.step("Get the IP Address of Virtual Machine:")
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    Case.expect(f"the vm ip is [{vm_ip}]", vm_ip != "")

    rcode, std_out, std_err = esxi.execute_vm_cmd(RHEL_VM_NAME, "yum list installed | grep -i stressapptest ",
                                                  timeout=60 * 3)
    if std_out == "":
        Case.step("Upload, install and compile stressapptest app:")
        rcode, std_out, std_err = esxi.execute_vm_cmd(RHEL_VM_NAME, "yum install gcc-c++ --allowerasing --nogpgcheck -y ",
                                                      timeout=60 * 3)
        Case.expect("yum install success!", std_err == "")
        esxi.execute_vm_cmd(RHEL_VM_NAME, f"unzip -o {tool}.zip", cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
        rcode, std_out, std_err = esxi.execute_vm_cmd(RHEL_VM_NAME, "chmod +777 configure "
                                                               "&& ./configure "
                                                               "&& make && make install",
                                                      cwd=TOOL_PATH, timeout=60 * 3)
        Case.expect("install stressapptest success ", rcode == 0)

    Case.step("Run the stress test:")
    esxi.execute_vm_cmd_async(RHEL_VM_NAME, r"stressapptest -s {} -M -m -W -l {}/stressapptest.log".
                                            format(stressapptest_run_time,
                                            sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')),
                                            timeout=60 * 3)
    Case.expect("run the stress app test success ", True)

    Case.step("Connect to vsphere:")

    esxi2 = get_vmmanger(sut2)
    Case.step("Move the VM to another datastore:")
    code, out, err = esxi2.execute_host_cmd_esxi(f"Move-VM -VM {RHEL_VM_NAME} -Datastore {datastore_name}", timeout=15 * 60)
    Case.expect("move vm success", err is None)
    Case.step("Check which datastore the migrated virtual machine is in:")
    code, out, err = sut.execute_shell_cmd("vim-cmd vmsvc/getallvms")
    Case.expect("the output success", err == "")
    Case.step("Back to the stress test and check whether the stress test is interrupted by the VM migration and wait "
              "for the stress test execution to complete.")
    Case.sleep(stressapptest_run_time + 100)
    rcode, std_out, std_err = esxi.execute_vm_cmd(RHEL_VM_NAME, "tail -n 10 stressapptest.log",
                                                  cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    result = log_check.scan_format("Status: %s", std_out)
    Case.expect("the test pass.", result[0] == "PASS")
    log_path = f"{LOG_PATH}\\results"
    os.mkdir(log_path)
    esxi.download_from_vm(RHEL_VM_NAME,
                          host_path=r"{}\stressapptest.log".format(log_path),
                          vm_path=r"{}/stressapptest.log".format(sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')))

    # restore
    Case.step("restore")
    code, out, err = esxi2.execute_host_cmd_esxi(f"Move-VM -VM {RHEL_VM_NAME} -Datastore datastore1", timeout=15 * 60)
    Case.expect("move vm success", err is None)
    code, out, err = esxi.execute_host_cmd_esxi(
        f"Remove-Datastore -Datastore {datastore_name} -VMHost {server_ip} -Confirm:$false", timeout=10 * 60)
    Case.expect('remove datastore successful', err is None)


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
