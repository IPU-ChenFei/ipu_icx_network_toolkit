"""
 @Case Link:https://hsdes.intel.com/appstore/article/#/1509886505
 @Author:
 @Prerequisite:
        1. Tools
            iso images
            anaconda-ks.cfg
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "The purpose of this test case is making sure creation of  VMs guests on KVM using Virt-Manager. "
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'rhel_iso.iso', sut_tool('VT_RHEL_ISO_L')))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("Use Below Command to Start VM installation")

    sut.upload_to_remote(PPEXPECT_PY, sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    sut.upload_to_remote(VM_CONNECT_PY, sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    cmd = common_cmd.static_cmd("ssh", ["ls"], "-ip \'localhost\'")
    code, out, err = sut.execute_shell_cmd(cmd, cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    Case.expect("ssh connect success! ", err == "")
    auto_cfg_path = f"{sut_tool('VT_TOOLS_L')}/linux_vm_kstart.cfg"
    vmname = "auto-" + str(int(time.time()))
    commands = f"virt-install --name={vmname} --memory=2048 --cpu=host-model-only --vcpu=2  " \
               f"--location={sut_tool('VT_RHEL_ISO_L')} " \
               f"--initrd-inject={auto_cfg_path} " \
               f"--disk path={sut_tool('VT_IMGS_L')}/{vmname}.qcow2,size=20 " \
               f"--network network=default " \
               f" --extra-args 'ks=file:linux_vm_kstart.cfg console=tty0 console=ttyS0,115200' --force --graphics none "

    cmd = common_cmd.answer_cmd("ssh root@localhost",
                                ["password: & password", f']# & {commands}[1200]', "Restarting guest.&"])

    code, out, err = sut.execute_shell_cmd(cmd, timeout=60 * 40, cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    Case.expect("auto install linux os successful ! ", err == "")
    kvm = get_vmmanger(sut)
    rcode = kvm.execute_vm_cmd(vmname, f'ifconfig')[0]
    Case.expect("Execute test command successfully", rcode == 0)
    kvm.undefine_vm(vmname)


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
