"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883699
 @Author:
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
            1. C:\BKCPkg\domains\virtualization\SGX.zip copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\Windows\tools\SGX.zip
        3. Files
            1. C:\BKCPkg\domains\virtualization\auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
    3. Virtual Machine
        1. A Windows virtual machine named "windows1"
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Add sgx drivers'
]


def test_steps(sut, my_os):
    #type: (SUT, GenericOS) -> None
    # Prepare steps - Enable VTD and VMX in BIOS
    Case.prepare('sgx enable after tme enable save and exit')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('enable_sgx_setting_xmlcli'))

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.precondition(FilePrecondition(sut, 'SGX.zip', sut_tool('VT_SGX_ZIP_W')))
    Case.check_preconditions()

    # Step 1 -
    Case.step('start VM')
    hyperv = get_vmmanger(sut)
    hyperv.start_vm(WINDOWS_VM_NAME, 600)

    # Step 2 -
    Case.step('Copy tool from HOST to SUT/from SUT to VM')
    hyperv.execute_vm_cmd(WINDOWS_VM_NAME, f"mkdir {sut_tool('SUT_TOOLS_VM_VIRTUALIZATION_W')}")
    hyperv.upload_to_vm(WINDOWS_VM_NAME, sut_tool('VT_SGX_ZIP_W'), f"{sut_tool('VT_VM_SGX_ZIP_W')}")

    # Step 3 -
    Case.step('Unzip Tools')
    sut.execute_shell_cmd('tar -zxf SGX.zip', cwd=sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION'), timeout=60)
    hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'tar -zxf SGX.zip', cwd=sut_tool('SUT_TOOLS_VM_VIRTUALIZATION_W'), timeout=60)

    # Step 4 -
    Case.step('set tool path')
    SGX_PSW_Path = f"{sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION')}\\SGX\\SGX-2.9*\\Installer\\PSW_INF"
    SGX_MPA_Path = f"{sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION')}\\SGX\\SGX-2.9*\\sgx_registrationagent_wins_2.9*\\"

    # Step 5 -
    Case.step('install SGX PSW in SUT')
    code, stdout, stderr = sut.execute_shell_cmd('pnputil /add-driver device/sgx_base.inf /install', cwd=SGX_PSW_Path,
                          timeout=180, powershell=True)
    Case.expect('execute command succeed', code==0)
    code, stdout, stderr = sut.execute_shell_cmd('pnputil /add-driver component/sgx_psw.inf /install', cwd=SGX_PSW_Path,
                          timeout=180, powershell=True)
    Case.expect('execute command succeed', code==0)
    my_os.warm_reset_cycle_step(sut)
    code, stdout, stderr = sut.execute_shell_cmd('tar -xzf MPA.zip', cwd=SGX_MPA_Path, timeout=60)
    Case.expect('execute command succeed', code==0)
    code, stdout, stderr = sut.execute_shell_cmd('pnputil /add-driver sgx_mpa.inf /install', cwd=SGX_MPA_Path,
                                          timeout=180, powershell=60)
    Case.expect('execute command succeed', code==0)
    cmd = "Get-WmiObject Win32_PNPEntity -Filter 'Name like  '\"%Guard%\"'' | select Name,Status"
    code, stdout, stderr = sut.execute_shell_cmd(cmd, timeout=60, powershell=True)
    Case.expect('execute command succeed', code==0)

    # Step 6 -
    Case.step('Enable VM SGX on SUT')
    Case.sleep(60)
    hyperv.shutdown_vm(WINDOWS_VM_NAME)
    code, stdout, stderr = sut.execute_shell_cmd('Import-Module .\EnableSGX-on-VM.psm1;'
                                                 f'Set-VMSgx -VmName {WINDOWS_VM_NAME} -SgxEnabled $True -SgxSize 32;'
                                                 f'Set-VMSgx -VmName {WINDOWS_VM_NAME} -SgxLaunchControlMode 2;',
                                                 cwd=sut_tool('VT_SGX_ROOT_W'), timeout=180, powershell=True)
    Case.expect('execute command succeed', code==0)

    Case.step("Install SGX PSW software within a virtual machine")
    hyperv.start_vm(WINDOWS_VM_NAME)
    code, stdout, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'pnputil /add-driver device/sgx_base.inf /install', cwd=SGX_PSW_Path,
                          timeout=180, powershell=True)
    Case.expect('execute command succeed', code==0)
    code, stdout, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'pnputil /add-driver component/sgx_psw.inf /install', cwd=SGX_PSW_Path,
                          timeout=180, powershell=True)
    Case.expect('execute command succeed', code == 0)

    code, stdout, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'tar -zxf MPA.zip', cwd=SGX_MPA_Path, timeout=60)
    Case.expect('execute command succeed', code==0)
    code, stdout, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'pnputil /add-driver sgx_mpa.inf /install', cwd=SGX_MPA_Path,
                                                 timeout=180, powershell=True)
    Case.expect('execute command succeed', code==0)

    Case.step("Check the device is OK in VM")
    cmd = "Get-WmiObject Win32_PNPEntity -Filter 'Name like  \\\"%Guard%\\\"' | select Name,Status"
    code, stdout, stderr = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, cmd, timeout=60, powershell=True)
    Case.expect('The device is ok in VM', "OK" in stdout)

    # Step 7 -
    Case.step('Restore Environment')
    hyperv.execute_vm_cmd(WINDOWS_VM_NAME, f"del {sut_tool('VT_VM_SGX_ZIP_W')}")
    Case.sleep(60)
    hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
    sut.execute_shell_cmd('Import-Module .\EnableSGX-on-VM.psm1;'
                          f'Set-VMSgx -VmName {WINDOWS_VM_NAME} -SgxEnabled $False -SgxSize 0;'
                          f'Set-VMSgx -VmName {WINDOWS_VM_NAME} -SgxLaunchControlMode 1;',
                          cwd=sut_tool('VT_SGX_ROOT_W'), timeout=180, powershell=True)
    set_bios_knobs_step(sut, *bios_knob('disable_sgx_setting_xmlcli'))


def clean_up(sut):
    if Result.returncode != 0:
        if Case.step_count >= 6:
            sut.execute_shell_cmd('Import-Module .\EnableSGX-on-VM.psm1;'
                                  f'Set-VMSgx -VmName {WINDOWS_VM_NAME} -SgxEnabled $False -SgxSize 0;'
                                  f'Set-VMSgx -VmName {WINDOWS_VM_NAME} -SgxLaunchControlMode 1;',
                                  cwd=sut_tool('VT_SGX_ROOT_W'), timeout=180, powershell=True)
        if 0 < Case.step_count:
            hyperv = get_vmmanger(sut)
            hyperv.execute_vm_cmd(WINDOWS_VM_NAME, f"del {sut_tool('VT_VM_SGX_ZIP_W')}")
            hyperv.shutdown_vm(WINDOWS_VM_NAME)
            set_bios_knobs_step(sut, *bios_knob('disable_sgx_setting_xmlcli'))
        else:
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
