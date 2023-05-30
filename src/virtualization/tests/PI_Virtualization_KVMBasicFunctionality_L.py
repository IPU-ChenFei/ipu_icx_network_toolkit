"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883465
 @Author:
 @Prerequisite:
    1. HW Configuration
        1. A X710 network card plug in PCIe, connect to external network with port 0
    2. SW Configuration
        1. SUT Python package
        2. Tools
        3. Files
            1. /home/BKCPkg/domains/virtualization/RHEL-8.4.0-20210503.1-x86_64-dvd1.iso copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\imgs\RHEL-8.4.0-20210503.1-x86_64-dvd1.iso
            2. /home/BKCPkg/domains/virtualization/imgs/win2k19.qcow2 copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\imgs\rwin2k19.qcow2
            3. /home/BKCPkg/domains/virtualization/linux_vm_kstart.cfg copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\linux_vm_kstart.cfg
            4. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Verify virtual OS(Linux and Windows) basic functionality through KVM console."
]

vm_name_l = f"auto_PI_rhel_{int(time.time())}"


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to os')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_virtual_common_xmlcli'))

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'rhel_iso.iso', sut_tool('VT_RHEL_ISO_L')))
    Case.precondition(FilePrecondition(sut, 'windows0.qcow2', sut_tool('VT_WINDOWS_TEMPLATE_L')))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    iso_path = sut_tool("VT_RHEL_ISO_L")
    kvm = get_vmmanger(sut)

    Case.step("create RHEL8 and linux vm")
    sut.upload_to_remote(PPEXPECT_PY, sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    sut.upload_to_remote(VM_CONNECT_PY, sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    cmd = common_cmd.static_cmd("ssh", ["pwd"], "-ip \'localhost\'")
    code, out, err = sut.execute_shell_cmd(cmd, cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    Case.expect("ssh connect success! ", err == "")

    auto_cfg_path = f"{sut_tool('VT_TOOLS_L')}/linux_vm_kstart.cfg"
    LINUX_COMMANDS = f"virt-install --name={vm_name_l} --memory=4096 --cpu=host-model-only --vcpu=2  " \
                     r"--location={} " \
                     f"--initrd-inject={auto_cfg_path} " \
                     f"--disk path={sut_tool('VT_IMGS_L')}/{vm_name_l}.qcow2,size=20 " \
                     f"--network network=default " \
                     f" --extra-args 'ks=file:linux_vm_kstart.cfg console=tty0 console=ttyS0,115200'" \
                     f" --force --graphics none"
    command = LINUX_COMMANDS.format(iso_path)
    cmd = common_cmd.answer_cmd("ssh root@localhost",
                                ["password: & password", f']# & {command}[1200]', "Restarting guest.& "])

    code, out, err = sut.execute_shell_cmd(cmd, timeout=60 * 40, cwd=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    Case.expect("auto install linux os successful ! ", err == "")
    Case.step("create windows and linux vm")
    if not kvm.is_vm_exist(WINDOWS_VM_NAME):
        kvm.create_vm_from_template(WINDOWS_VM_NAME, TEMPLATE, vnic_type='\"e1000\"')
    kvm.start_vm(WINDOWS_VM_NAME)
    kvm.execute_vm_cmd(WINDOWS_VM_NAME, "ipconfig", timeout=60 * 3)

    repeat_times = 1
    Case.step("reboot the vm three times")
    for i in range(repeat_times):
        Case.expect(f"vm reboot cycle {i}", True)
        logger.info(f"vm reboot cycle {i} started")
        kvm.reboot_vm(vm_name_l)
        code, out, err = kvm.execute_vm_cmd(vm_name_l, "ifconfig")
        Case.expect(f"VM: [{vm_name_l}] reboot successful!", err == "")
        kvm.reboot_vm(WINDOWS_VM_NAME)
        rcode, std_out, std_err = kvm.execute_vm_cmd(WINDOWS_VM_NAME, "ipconfig", timeout=60 * 3)
        Case.expect(f"VM: [{WINDOWS_VM_NAME}] reboot successful!", std_err == "")
        Case.sleep(30)
        logger.info(f"vm reboot cycle {i} succeed")

    Case.step("shutdown -r -t 0 the vm three times")
    for i in range(repeat_times):
        Case.expect(f"cycle {i}", True)
        logger.info(f"vm shutdown and start cycle {i} started")
        kvm.shutdown_vm(vm_name_l)
        kvm.start_vm(vm_name_l)
        code, out, err = kvm.execute_vm_cmd(vm_name_l, "ifconfig")
        Case.expect(f"VM: [{vm_name_l}] shutdown successful!", err == "")
        kvm.shutdown_vm(WINDOWS_VM_NAME)
        kvm.start_vm(WINDOWS_VM_NAME)
        rcode, std_out, std_err = kvm.execute_vm_cmd(WINDOWS_VM_NAME, "ipconfig", timeout=60 * 3)
        Case.expect(f"VM: [{WINDOWS_VM_NAME}] shutdown successful!", std_err == "")
        Case.sleep(30)
        logger.info(f"vm shutdwon and start cycle {i} succeed")

    Case.step("reboot the sut three times")
    for i in range(repeat_times):
        Case.expect("cycle {i}", True)
        logger.info(f"sut reboot cycle {i} started")
        my_os.warm_reset_cycle_step(sut)
        code, out, err = sut.execute_shell_cmd("ifconfig")
        Case.expect("SUT reboot successful !", err == "")
        logger.info(f"sut reboot cycle {i} succeed")

    Case.step("shutdown the sut three times")
    for i in range(repeat_times):
        logger.info(f"sut shutdown and start cycle {i} started")
        sut.ac_off()
        sut.ac_on()
        Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
        code, out, err = sut.execute_shell_cmd("ifconfig")
        Case.expect("SUT shutdown successful !", err == "")
        logger.info(f"sut shutdown and start cycle {i} succeed")

    Case.sleep(30)
    kvm.undefine_vm(vm_name_l)
    kvm.undefine_vm(WINDOWS_VM_NAME)


def clean_up(sut):
    if Result.returncode != 0:
        kvm = get_vmmanger(sut)
        for vm in [vm_name_l, WINDOWS_VM_NAME]:
            if kvm.is_vm_exist(vm):
                kvm.shutdown_vm(vm)
                kvm.undefine_vm(vm)


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
