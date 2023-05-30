import re
import time
from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEVOp
from src.mev.lib.config import *
from src.configuration.config.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV, SUT_IMAGE_LINUX_MEV, SUT_TMP_LINUX_MEV

CASE_DESC = [
    'Set BKC environment',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def set_static(sut, eth_name):
    ifcfg = f'/etc/sysconfig/network-scripts/ifcfg-{eth_name}'
    ret, _, _ = sut.execute_shell_cmd(f"echo 'TYPE=Ethernet \n"
                                      f"PROXY_METHOD=none \n"
                                      f"BROWSER_ONLY=no \n"
                                      f"BOOTPROTO=static \n"
                                      f"DEFROUTE=yes \n"
                                      f"IPV4_FAILURE_FATAL=no \n"
                                      f"IPV6INIT=yes \n"
                                      f"IPV6_AUTOCONF=yes \n"
                                      f"IPV6_DEFROUTE=yes \n"
                                      f"IPV6_FAILURE_FATAL=no \n"
                                      f"IPV6_ADDR_GEN_MODE=stable-privacy \n"
                                      f"NAME={eth_name} \n"
                                      f"IPADDR=100.0.0.1 \n"
                                      f"NETMASK=255.255.255.0 \n"
                                      f"DEVICE={eth_name} \n"
                                      f"ONBOOT=yes \n' > {ifcfg}")
    sut.execute_shell_cmd(f'ifup {eth_name}')
    ret, _, _ = sut.execute_shell_cmd('ping -c 3 -I 100.0.0.1 100.0.0.100', timeout=20)
    return ret == 0


def set_dhcp(sut, eth_name):
    ifcfg = f'/etc/sysconfig/network-scripts/ifcfg-{eth_name}'
    ret, _, _ = sut.execute_shell_cmd(f"echo 'TYPE=Ethernet \n"
                                      f"PROXY_METHOD=none \n"
                                      f"BROWSER_ONLY=no \n"
                                      f"BOOTPROTO=dhcp \n"
                                      f"DEFROUTE=yes \n"
                                      f"IPV4_FAILURE_FATAL=no \n"
                                      f"IPV6INIT=yes \n"
                                      f"IPV6_AUTOCONF=yes \n"
                                      f"IPV6_DEFROUTE=yes \n"
                                      f"IPV6_FAILURE_FATAL=no \n"
                                      f"NAME={eth_name} \n"
                                      f"DEVICE={eth_name} \n"
                                      f"ONBOOT=yes \n' > {ifcfg}")
    sut.execute_shell_cmd(f'ifup {eth_name}')
    Case.sleep(10)
    _, out, _ = sut.execute_shell_cmd(f'ifconfig {eth_name}')
    try:
        ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', out, re.I).group()
        return ip
    except AttributeError:
        return None


def get_version(sut, name, end_pattern):
    _, output, _ = sut.execute_shell_cmd(f"ls | grep {name}", cwd=SUT_TOOLS_LINUX_MEV)
    out_list = output.split("\n")
    return [out.replace(end_pattern, "") for out in out_list if out.endswith(end_pattern)]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # TODO, replace these with your own steps
    # Prepare steps - call predefined steps
    sut.ac_off()
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    sut.execute_uefi_cmd('FS0:')
    sut.execute_uefi_cmd(r'EFI\BOOT\BOOTX64.EFI', timeout=0)
    Case.wait_and_expect('OS install successfully', timeout=3600, function=sut.check_system_in_os)
    _, out, _ = sut.execute_shell_cmd("lsusb -t | grep -i 'Driver=hub/4p, 480M' | awk '{print $3}'")
    out = out.split('\n')
    flag = False
    for usb in out:
        if not usb:
            continue
        usb = usb.strip(":")
        _, eth_name, _ = sut.execute_shell_cmd(f"ls /sys/bus/usb/devices/1-{usb}.1:1.0/net")
        if not flag:
            if set_static(sut, eth_name):
                flag = True
            else:
                set_dhcp(sut, eth_name)
        else:
            set_dhcp(sut, eth_name)

    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sut.execute_shell_cmd(f'date -s "{now}"')
    sut.execute_shell_cmd(f'hwclock -w')
    sut.execute_shell_cmd(f'hwclock -s')
    sut.execute_shell_cmd(f'mkdir -p {SUT_TMP_LINUX_MEV}')

    host_package = f'{SUT_IMAGE_LINUX_MEV}/{stepping}_{CI}/host/packages/mev_hw_{stepping}_fedora30'
    MEVOp.download_ci(sut, ci_id=CI, release_type='release', ci_type='ci')
    sut.execute_shell_cmd('rpm -iUvh kernel-headers*.rpm', timeout=300, cwd=host_package)
    sut.execute_shell_cmd('rpm -iUvh kernel-devel*.rpm', timeout=300, cwd=host_package)
    ret, _, _ = sut.execute_shell_cmd('rpm -iUvh kernel-5.*.rpm', timeout=300, cwd=host_package)
    Case.expect('install ATE kernel', ret == 0)
    _, out, _ = sut.execute_shell_cmd("grubby --info=ALL")
    kernel = re.search(r'kernel="/boot/vmlinuz-5.10.\S*"', out, re.I).group()
    sut.execute_shell_cmd(f"grubby --set-default {kernel}")
    sut.execute_shell_cmd(f"sed -i 's/rhgb/iommu=on intel_iommu=on intel_ate=on rhgb/g' /etc/default/grub")
    ret, _, _ = sut.execute_shell_cmd('grub2-mkconfig -o /boot/efi/EFI/centos/grub.cfg')
    Case.expect('modify grub', ret == 0)
    my_os.warm_reset_cycle_step(sut, timeout=1800)
    #
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sut.execute_shell_cmd(f'date -s "{now}"')
    sut.execute_shell_cmd(f'hwclock -w')
    sut.execute_shell_cmd(f'hwclock -s')
    ret, _, _ = sut.execute_shell_cmd(f'rpm -ivh lan-cp*.rpm', cwd=host_package)
    Case.expect('install LAN-CP', ret == 0)
    ret, _, _ = sut.execute_shell_cmd(f'rpm -ivh lce-0*.rpm', cwd=host_package)
    Case.expect('install LCE', ret == 0)
    ret, stdout, _ = sut.execute_shell_cmd('rpm -ivh nvme-*.rpm', 30, cwd=host_package)
    Case.expect('install NVMe', ret == 0)
    # install tools
    sut.execute_shell_cmd('dos2unix install_tool.sh', cwd='/opt/APP')
    sut.execute_shell_cmd(f"./install_tool.sh", timeout=600, cwd='/opt/APP')


def clean_up(sut):
    pass


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
