"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509876227
 @Author:QiBo
 @Prerequisite:
         ESXi installed on SUT
    1. HW Configuration
        Plug 1 NVMe SSD into SUT
    2. SW Configuration
        1. Tools
            Install Power CLI on local Windows host
                Install-Module VMware.PowerCLI -Force
        2. Files

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "VMM allows a VM to be saved to disk and resumed after the platform goes through a power-cycle. Verify that they "
    "function as expected"
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'vmd.zip', sut_tool('VT_VMD_V')))
    Case.check_preconditions()

    Case.step("Check for the vmd drives and controllers:")
    ret, res, err = sut.execute_shell_cmd("esxcfg-scsidevs -a")
    Case.expect("Check for the vmd drives and controllers pass", ret == 0)

    Case.step("Check whether driver version:")
    ret, res, err = sut.execute_shell_cmd("esxcli software vib list | grep vmd")
    Case.expect("Check whether driver version:", INTEL_NVME_VMD in res)

    Case.step("Remove the NVMe driver:")
    ret, res, err = sut.execute_shell_cmd(f"esxcli software vib remove -n {INTEL_NVME_VMD}")
    res1 = log_check.find_lines("completed successfully", res)
    VIB = log_check.find_lines("VIBs Removed", res)
    Case.expect(f"{VIB} successfully", res1)

    Case.step("Reboot the system")
    sut.execute_shell_cmd('reboot')
    Case.sleep(3 * 60)
    Case.wait_and_expect(f'OS for system back to os', 60 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.step("check remove driver")
    ret, res, err = sut.execute_shell_cmd("esxcli software vib list | grep vmd")
    res1 = log_check.find_keyword(INTEL_NVME_VMD, res)
    Case.expect("Check remove driver version not exist pass", not res1)

    Case.step("Check for the vmd drives and controllers:")
    ret, res, err = sut.execute_shell_cmd("esxcfg-scsidevs -a")
    iavmd = log_check.find_lines("iavmd", res)
    Case.expect("Check for the vmd drives and controllers not exist pass", not iavmd)
    ret, res, err = sut.execute_shell_cmd('esxcli system maintenanceMode set --enable no')
    Case.expect("Exit the system maintenance mode pass", err == "")

    Case.step("Exit the system maintenance mode:")
    code, out, err = sut.execute_shell_cmd('esxcli system maintenanceMode set --enable no')
    Case.expect("Maintenance mode is disabled. ", err == "")


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
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
