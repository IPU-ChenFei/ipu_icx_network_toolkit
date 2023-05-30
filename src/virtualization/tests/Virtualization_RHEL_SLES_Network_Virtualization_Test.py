"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509886035
 @Author: Wang, Guangyu
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools

        3. Files
            1. /home/BKCPkg/domains/virtualization/imgs/rhel0.qcow2 copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\imgs\rhel0.qcow2
            2. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
            3. /home/BKCPkg/domains/virtualization/tools/vnstat-1.11.tar.gz copy from
                \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\tools\vnstat-1.11.tar.gz
        4. virtual bridge
            create virtual bridge named br0
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Perform basic network virtualization tests on Hypervisor and guests VMs in order to validate network traffic is "
    "flowing between the virtual machines and the external network "
]


def check_iperf_log(sut, log_path):
    filename = os.path.join(LOG_PATH, log_path.split("/")[-1])
    sut.download_to_local(log_path, filename)
    with open(filename, "r") as file:
        content = file.readlines()
    if len(content) == 0:
        return False
    return "Done" in content[-1]


def get_block(out_lines, index):
    block = {}
    block["name"] = out_lines[index].split(":")[0]
    block["ip"] = ""
    if "inet" in out_lines[index+1] and "netmask" in out_lines[index+1]:
        block["ip"] = out_lines[index+1].split()[1]
    return block


def split_ifconfig_blocks(output):
    out_lines = output.splitlines()
    blocks = []
    i = 0
    while i < len(out_lines):
        if "flags" in out_lines[i]:
            blocks.append(get_block(out_lines, i))
            while i < len(out_lines) and out_lines[i].strip() != "":
                i += 1
        i += 1
    return blocks


def get_bridge_network_adpater_in_vm(kvm, vm_name):
    _, std_out, _ = kvm.execute_vm_cmd(vm_name, "ifconfig")
    ip_blocks = split_ifconfig_blocks(std_out)

    for block in ip_blocks:
        if "lo" in block["name"] or "vir" in block["name"]:
            continue
        if block["ip"] == "" or block["ip"] == VM_BRO_IP:
            return block["name"]
    raise Exception(f"error: cannot get bridge network adpater in {vm_name}, check if bridge has been attached or not")


def set_vm_adapter_ip(kvm, adatper_name):
    cmd = f"nmcli conn show | grep {adatper_name}"
    std_out = kvm.execute_vm_cmd(RHEL_VM_NAME, cmd)[1]
    if adatper_name in std_out:
        old_uuid = std_out.strip().split()[-3]
        cmd = f"nmcli conn delete {old_uuid}"
        kvm.execute_vm_cmd(RHEL_VM_NAME, cmd)
    cmd = f"nmcli conn add type ethernet con-name {adatper_name} ifname {adatper_name} ipv4.addr {VM_BRO_IP}/24 ipv4.method manual method none"
    cmd += f" && nmcli conn up {adatper_name}"
    kvm.execute_vm_cmd(RHEL_VM_NAME, cmd)


def remove_vm_adapter_ip(kvm ,adapter_name):
    cmd = f"nmcli conn show | grep {adapter_name}"
    std_out = kvm.execute_vm_cmd(RHEL_VM_NAME, cmd)[1]
    if adapter_name not in std_out:
        logger.info(f"Cannot find {adapter_name} in VM")
        return

    cmd = f"nmcli conn delete "


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None
    Case.prepare('boot to os')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob("enable_vmx_xmlcli"), *bios_knob("enable_vtd_xmlcli"))

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(BridgePrecondition(sut, 'br0'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    Case.step("Verify libvirtd daemon is running and enable on the system")
    sut.execute_shell_cmd('systemctl enable libvirtd')
    sut.execute_shell_cmd('systemctl start libvirtd')
    code, out, err = sut.execute_shell_cmd('systemctl status libvirtd')
    Case.expect("The CLI exec successfully and returns a zero return code", err == '')

    Case.step("Setup br0 on SUT")
    cmd = "ifconfig br0 up &&"
    cmd += f"ip a add {SUT_BR0_IP}/24 dev br0"
    rcode, _, _ = sut.execute_shell_cmd(cmd)
    _, std_out, _ = sut.execute_shell_cmd("ifconfig br0 | grep inet | grep -v inet6")
    Case.expect(f"Set br0's ip to {SUT_BR0_IP} successfully", SUT_BR0_IP in std_out)

    Case.step("Install iperf3 on SUT")
    rcode = sut.execute_shell_cmd("yum -y install iperf3")[0]
    Case.expect("iperf3 successfully install on SUT", rcode == 0)

    Case.step("Attach bridge interface to virtual machine")
    _, std_out, _ = sut.execute_shell_cmd(
        f'virsh attach-interface {RHEL_VM_NAME} --type bridge --source br0 --model virtio --config')
    Case.expect("Command execute successfully", "Interface attached successfully" in std_out)

    Case.step("Check if bridge has been attached to virtual machine")
    _, std_out, _ = sut.execute_shell_cmd(f'virsh domiflist {RHEL_VM_NAME} | grep -i br0')
    Case.expect(f"Virtual bridge br0 has been attached to {RHEL_VM_NAME}", std_out.strip() != "")

    Case.step("Setup network adpater attached")
    kvm = get_vmmanger(sut)
    kvm.start_vm(RHEL_VM_NAME)
    target_net = get_bridge_network_adpater_in_vm(kvm, RHEL_VM_NAME)
    set_vm_adapter_ip(kvm, target_net)
    _, std_out, _ = kvm.execute_vm_cmd(RHEL_VM_NAME, f"ifconfig {target_net} | grep inet | grep -v inet6")
    Case.expect(f"Set {target_net} ip to {VM_BRO_IP} successfully", VM_BRO_IP in std_out)

    Case.step(f"Install iperf on {RHEL_VM_NAME}")
    rcode = kvm.execute_vm_cmd(RHEL_VM_NAME, "yum -y install iperf3")[0]
    Case.expect(f"iperf3 successfully install on {RHEL_VM_NAME}", rcode == 0)

    Case.step("From SUT connect to the VM that is running the iperf3 server dameon")
    kvm.execute_vm_cmd(RHEL_VM_NAME, f"iperf3 -s -D")
    std_out = kvm.execute_vm_cmd(RHEL_VM_NAME, "ps aux | grep -i iperf | wc -l")[1]
    Case.expect(f"iperf server on {RHEL_VM_NAME} started successfully", int(std_out) > 1)
    sut.execute_shell_cmd(f"iperf3 -c {VM_BRO_IP} -f g -t 60 -i 60 -P 3 --len 1M -Z --logfile /home/iperf_sut.log", timeout=120)

    Case.step("Launch command to send traffic back from server to client")
    sut.execute_shell_cmd("iperf3 -s -D")
    std_out = sut.execute_shell_cmd("ps aux | grep -i iperf | wc -l")[1]
    Case.expect("iperf server on SUT started successfully", int(std_out) > 1)
    _, std_out, _ = kvm.execute_vm_cmd(RHEL_VM_NAME,
                       f"iperf3 -c {SUT_BR0_IP} -f g -t 60 -i 60 -P 3 --len 1M -Z -R --logfile /home/iperf_vm.log")

    Case.step("Check if the iperf log is correct")
    kvm.download_from_vm(RHEL_VM_NAME, "/home/iperf_vm.log", "/home/iperf_vm.log")
    Case.expect("SUT iperf log no error", check_iperf_log(sut, "/home/iperf_sut.log"))
    Case.expect("VM iperf log no error", check_iperf_log(sut, "/home/iperf_vm.log"))

    Case.step("Restore environment")
    kvm.execute_vm_cmd(RHEL_VM_NAME, "rm -f /home/iperf_vm.log")
    kvm.execute_vm_cmd(RHEL_VM_NAME, f"nmcli conn delete {target_net}")
    kvm.shutdown_vm(RHEL_VM_NAME)
    sut.execute_shell_cmd("ifconfig br0 up 0")
    sut.execute_shell_cmd("rm -f /home/iperf_vm.log")
    sut.execute_shell_cmd("rm -f /home/iperf_sut.log")
    sut.execute_shell_cmd(f'virsh detach-interface {RHEL_VM_NAME} --type bridge --config')


def clean_up(sut):
    if Result.returncode != 0:
        if Case.step_count < 1 and Case.prepare_count < 4:
            cleanup.to_s5(sut)
            return
        kvm = get_vmmanger(sut)
        if Case.step_count >= 3:
            sut.execute_shell_cmd("ifconfig br0 up 0")
        if Case.step_count >= 4:
            sut.execute_shell_cmd(f'virsh detach-interface {RHEL_VM_NAME} --type bridge --config')
        if Case.step_count >= 10:
            sut.execute_shell_cmd("rm -f /home/iperf_vm.log")
            sut.execute_shell_cmd("rm -f /home/iperf_sut.log")
            kvm.execute_vm_cmd(RHEL_VM_NAME, "rm -f /home/iperf_vm.log")
        try:
            target_net = get_bridge_network_adpater_in_vm(kvm, RHEL_VM_NAME)
            kvm.execute_vm_cmd(RHEL_VM_NAME, f"nmcli conn delete {target_net}")
        except Exception:
            pass
        kvm.shutdown_vm(RHEL_VM_NAME)


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
