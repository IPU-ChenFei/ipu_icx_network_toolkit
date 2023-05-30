"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509882208
 @Author:YanXu
 @Prerequisite:
    1. HW Configuration
        1.Plug 2 NVMe SSD into SUT
    2. SW Configuration
        1. SUT Python package
        2. Tools
        3. Files
            1. intel-nvme-vmd-en_2.0.0.1146-1OEM.700.1.0.15843807_16259168-package.zip
    3. Virtual Machine

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Verify VMD driver installation based on a bootable ESXi system."
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("Boot to ESXi")
    boot_to(sut, sut.default_os)

    Case.prepare("Check preconditions")
    Case.precondition(HostFilePrecondition(sut, 'intel_nvme_vmd.zip', sut_tool('VT_INTEL_NVME_VMD_H')))
    Case.check_preconditions()

    Case.prepare(f"Upload {PrecondInfo.INTEL_NVME_VMD_H['name']}")
    sut.upload_to_remote(sut_tool("VT_INTEL_NVME_VMD_H"), '/', timeout=20)

    Case.step("Check whether the installation file was uploaded successfully:")
    _, check_file, _ = sut.execute_shell_cmd('ls')
    Case.expect('The list contains the file name', INTEL_NVME_ZIP in check_file)

    Case.step("Check for the vmd drives and controllers")
    _, check_vmd, _ = sut.execute_shell_cmd('esxcfg-scsidevs -a')
    Case.expect('intel-nvme-vmd tool be not in', INTEL_NVME_VMD not in check_vmd)

    Case.step("Set system as maintenance mode")
    set_maintenance, _, _ = sut.execute_shell_cmd('esxcli system maintenanceMode set --enable yes')
    Case.expect('Maintenance mode is enabled', set_maintenance == 0)

    Case.step("Unzip the NVMe driver installation package to a new folder")
    sut.execute_shell_cmd(f'mkdir {MKDIR_NAME}')
    _, intel_nvme_vib, _ = sut.execute_shell_cmd(f'unzip -d {MKDIR_NAME}/ {INTEL_NVME_ZIP}', timeout=20)
    Case.expect('unzip successfully', INTEL_NVME_VIB in intel_nvme_vib)

    Case.step("Install the Driver")
    _, install_nvme, _ = sut.execute_shell_cmd(f'esxcli software vib install -v /{MKDIR_NAME}/{INTEL_NVME_VIB} --no-sig-check', timeout=100)
    Case.expect('VIBs Installed: INT_bootbank_intel-nvme-vmd_2.0.0.1146-1OEM.700.1.0.15843807', VIBS_INSTALLED in install_nvme)

    Case.step("Reboot the system")
    sut.execute_shell_cmd('reboot')
    Case.sleep(3 * 60)
    Case.wait_and_expect(f'OS for system back to os', 60 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.step("Check whether the driver was installed and verify the driver version")
    _, install_nvme_vmd, _ = sut.execute_shell_cmd('esxcli software vib list | grep vmd', timeout=10)
    Case.expect('intel-nvme-vmd installed successfully', INTEL_NVME_VMD in install_nvme_vmd)
    
    Case.step("Check for the vmd drives and controllers")
    _, check_vmd, _ = sut.execute_shell_cmd('esxcfg-scsidevs -a')
    Case.expect('intel-nvme-vmd install successfully', INTEL_NVME_VMD in check_vmd)

    Case.step("Set system as maintenance mode")
    set_maintenance, _, _ = sut.execute_shell_cmd('esxcli system maintenanceMode set --enable no')
    Case.expect('Maintenance mode is enabled', set_maintenance == 0)


def clean_up(sut):
    if Result.returncode != 0:
        sut.execute_shell_cmd('esxcli system maintenanceMode set --enable no')
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
        # clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)