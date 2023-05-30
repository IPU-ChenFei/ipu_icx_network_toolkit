"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883718
 @Author:Liu, JianjunX
 @Prerequisite:
    1. SW Configuration
        1. Tools
            SGX folder
            SGXFunctionalValidation_v0.8.9.0.tar.gz
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "When SGX feature is enabled,  Windows Hyper-V, "
    "Linux KVM/Xen VMMs shouldn't have any issues with CPU and IO virtualization"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('enable_sgx_setting_xmlcli'))

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'SGX/', sut_tool('VT_SGX_ROOT_L')))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    tool = sut_tool("VT_SGXFUNCTIONALVALIDATION_L")
    SGX_FUNC_TOOL = tool.split("/")[-1]
    SGX_FUNC_PATH = SGX_FUNC_TOOL.split(".tar.gz")[0]

    Case.step(f"Install SGX Driver")
    # date -s “2008-08-08 12:00:00″
    sut.execute_shell_cmd("yum -y install openssl-devel libcurl-devel protobuf-devel yum-utils", timeout=60 * 3)
    sut.execute_shell_cmd(f"mkdir -p {sut_tool('VT_SGX_ROOT_L')}", cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    sut.execute_shell_cmd(f"chmod +x {sut_tool('VT_SGX_DRIVER_BIN_L')}", cwd=sut_tool('VT_SGX_ROOT_L'))
    code, out, err = sut.execute_shell_cmd(f"{sut_tool('VT_SGX_DRIVER_BIN_L')}", cwd=sut_tool('VT_SGX_ROOT_L'),timeout=60 * 3)
    Case.expect("Install SGX Driver successful! ", code == 0)

    Case.step("Verify SGX is on")
    sut.execute_shell_cmd("ls -la /dev/sgx*")

    Case.step("Install SGX SDK")
    sut.upload_to_remote(SGX_INSTALL, sut_tool('VT_SGX_ROOT_L'))
    sut.upload_to_remote(PPEXPECT_PY, sut_tool('VT_SGX_ROOT_L'))
    code, out, err = sut.execute_shell_cmd(f"python sgx_install.py install_sgx localhost", timeout=60 * 2,
                                           cwd=sut_tool('VT_SGX_ROOT_L'))
    Case.expect("Install SGX SDK successful! ", code == 0)

    Case.step("Install SGX User mode software")
    # cd /opt/intel
    sut.execute_shell_cmd(f"cp -r {SGX_RPM_LOCAL_REPO} {SGX_REPO_PATH}", cwd=sut_tool('VT_SGX_ROOT_L'))
    sut.execute_shell_cmd(f"tar -xvf {SGX_RPM_LOCAL_REPO}", cwd=SGX_REPO_PATH)
    code, out, err = sut.execute_shell_cmd(
        f"dnf -y --nogpgcheck --repofrompath=SGX,{SGX_REPO_PATH}/sgx_rpm_local_repo install libsgx-urts "
        "libsgx-launch libsgx-epid libsgx-quote-ex libsgx-dcap-ql libsgx-uae-service", timeout=60 * 2,
        cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    Case.expect("Install SGX User mode software successful! ", code == 0)

    Case.step("Unzip the Tool, Run the Intel FVT (Function Validation) tool to ensure "
              "that without virtualization SGX can be enabled and used.")
    sut.execute_shell_cmd(f"tar -zxvf {SGX_FUNC_TOOL}", cwd=sut_tool('VT_SGX_ROOT_L'))
    code, out, err = sut.execute_shell_cmd(f"cd {SGX_FUNC_PATH} "
                                           f"&& {FUNC_CMD}", cwd=sut_tool('VT_SGX_ROOT_L'))
    res1 = log_check.find_keyword("FAILURE", out)
    res2 = log_check.find_keyword("SGX is disabled", out)
    res3 = log_check.find_keyword("SUCCESS", out)
    Case.expect("Install SGX software successful! ", len(res3) != 0 and len(res1) == 0 and len(res2) == 0)

    Case.step("Restore SGX BIOS setting")
    try:
        set_bios_knobs_step(sut, *bios_knob('disable_sgx_setting_xmlcli'))
    except Exception:
        sut.ac_off()
        sut.ac_on()


def clean_up(sut):
    if Result.returncode != 0:
        if 0 <= Case.step_count < 6:
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
