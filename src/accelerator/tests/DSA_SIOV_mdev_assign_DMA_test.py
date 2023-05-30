import time
# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'Check QAT device',
    'QAT driver install',
    'check cpa_sample_code file generate'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    qemu = RichHypervisor(sut)

    Case.prepare('boot to OS with bios knobs modified')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_dsa_commom_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # step 2
    Case.step('copy spr acce random tool and OVFM tool to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30*60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10*60, cwd='/home/')
    # sut.execute_shell_cmd('mv centos*.img centos.img', timeout=10*60, cwd='/home/')
    # sut.execute_shell_cmd(f'cp {IMAGE_PATH_L}centos_base.qcow2 /home/centos.img', timeout=10*60)
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=SPR_ACCE_RANDOM_CONFIG_PATH_L)

    # step 3
    Case.step('Modify config file and install dsa tool')
    sut.execute_shell_cmd('unzip *.zip', timeout=5*60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    _, out, err = sut.execute_shell_cmd('cat config.sh', timeout=60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
    line_list = out.strip().split('/root/images/')
    image_name = line_list[1].split('" # location of VM guest image')[0]
    sut.execute_shell_cmd(f'sed -i "s/\/root\/images\/{image_name}/\/home\/BKCPkg\/domains\/accelerator\/imgs\/centos.qcow2/g" {SPR_ACCE_RANDOM_CONFIG_PATH_L}*/config.sh', timeout=60)
    sut.execute_shell_cmd(f'sed -i "s/\/usr\/share\/qemu\/OVMF.fd/\/home\/OVMF.fd/g" {SPR_ACCE_RANDOM_CONFIG_PATH_L}*/config.sh', timeout=60)
    acce.accel_config_install()
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', True)
    else:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl', True)

    # step 4
    Case.step('Install sut environments')
    sut.execute_shell_cmd('python -m pip install --upgrade pip', timeout=10*60)
    sut.execute_shell_cmd('python -m pip install --upgrade paramiko', timeout=10*60)
    sut.execute_shell_cmd(f'mkdir {SRC_SCRIPT_PATH_L}')
    sut.execute_shell_cmd(f'rm -rf {SRC_SCRIPT_PATH_L}*')
    sut.upload_to_remote(localpath=SRC_SCRIPT_H, remotepath=SRC_SCRIPT_PATH_L)
    sut.execute_shell_cmd('unzip *', timeout=60 * 5, cwd=SRC_SCRIPT_PATH_L)
    sut.execute_shell_cmd('chmod 777 *', timeout=60 * 5, cwd=f'{SRC_SCRIPT_PATH_L}*/')

    def launch_vm_command():
        _, out, err = sut.execute_shell_cmd('./Setup_Randomize_DSA_Conf.sh -maM', timeout=10*60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        line_list = out.strip().split('To launch VM:')
        print(line_list)
        return line_list[1]

    # step 5
    Case.step('Launch VM')
    # launch_vm_command = '/home/BKCPkg/domains/accelerator/spr_acce_random_config/spr-accelerators-random-config-and-test-master/logs/DSA_MDEV-20220219-144640/launch_vm.sh'
    launch_vm_command = launch_vm_command()
    sut.execute_shell_cmd_async(f'{launch_vm_command}')
    time.sleep(120)

    # step 6
    Case.step('Install rpm files')
    vm_name = 'guestVM1'
    qemu.create_exist_vm(vm_name)
    qemu.execute_vm_cmd(vm_name, 'cat /proc/cmdline')
    acce.rpm_install_vm(qemu, vm_name)
    acce.kernel_header_devel_vm(qemu, vm_name)
    ret, _, _ = qemu.execute_vm_cmd(vm_name, f"yum groupinstall -y \'Development Tools\' --allowerasing", timeout=10*60)
    Case.expect('yum install Development Tools pass', ret == 0)
    qemu.execute_vm_cmd(vm_name, 'yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools', timeout=10*60)
    qemu.execute_vm_cmd(vm_name, 'yum install -y asciidoc xmlto libuuid-devel json-c-devel kmod-devel libudev-devel', timeout=10*60)
    # acce.modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', True)
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        acce.modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', True)
    else:
        acce.modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on no5lvl', True)


    def tool_upload(qemu, vm_name):
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {DSA_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {DSA_PATH_L}*', timeout=60)
        sut_file_dir = f'{DSA_PATH_L}{DSA_ACCEL_CONFIG_NAME}'
        vm_file_dir = f'{DSA_PATH_L}{DSA_ACCEL_CONFIG_NAME}'
        sut.upload_to_remote(localpath=DSA_H, remotepath=DSA_PATH_L)
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {SPR_ACCE_RANDOM_CONFIG_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {SPR_ACCE_RANDOM_CONFIG_PATH_L}*', timeout=60)
        sut_file_dir1 = f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}{SPR_ACCE_RANDOM_CONFIG_NAME}'
        vm_file_dir1 = f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}{SPR_ACCE_RANDOM_CONFIG_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir1, vm_file_dir1)
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {KERNEL_INTERNAL_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {KERNEL_INTERNAL_PATH_L}*', timeout=60)
        sut_file_dir2 = f'{KERNEL_INTERNAL_PATH_L}{KERNEL_INTERNAL_NAME}'
        vm_file_dir2 = f'{KERNEL_INTERNAL_PATH_L}{KERNEL_INTERNAL_NAME}'
        sut.upload_to_remote(localpath=KERNEL_INTERNAL_H, remotepath=KERNEL_INTERNAL_PATH_L)
        qemu.upload_to_vm(vm_name, sut_file_dir2, vm_file_dir2)

    def check_error(err):
        if err != '':
            logger.error(err)
            raise Exception(err)

    # step 7
    Case.step('Install DSA tool in VM')
    tool_upload(qemu, vm_name)
    _, out, err = qemu.execute_vm_cmd(vm_name, 'accel-config --version')
    if 'command not found' in err:
        qemu.execute_vm_cmd(vm_name, 'unzip *.zip', cwd=f'{DSA_PATH_L}')
        _, out, err = qemu.execute_vm_cmd(vm_name, './autogen.sh', timeout=10*60, cwd=f'{DSA_PATH_L}*/')
        # check_error(err)
        _, out, err = qemu.execute_vm_cmd(vm_name, "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 --enable-test=yes", timeout=10 * 60, cwd=f'{DSA_PATH_L}*/')
        _, out, err = qemu.execute_vm_cmd(vm_name, 'make', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        check_error(err)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'make check', timeout=50 * 60, cwd=f'{DSA_PATH_L}*/')
        check_error(err)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'make install', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        check_error(err)

    # step 8
    Case.step('Run DSA random test')
    qemu.execute_vm_cmd(vm_name, 'unzip *.zip', cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}')
    _, out, err = qemu.execute_vm_cmd(vm_name, './Guest_Mdev_Randomize_DSA_Conf.sh -k', timeout=10 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
    check_error(err)
    cpu_num = acce.get_cpu_num()
    line_list = out.strip().split('Enabling work-queues:')
    enabled_device_num = line_list[1].count('dsa')
    if enabled_device_num != cpu_num*acce.dsa_device_num:
        logger.error('Not all DSA wq are enabled')
        raise Exception('Not all DSA wq are enabled')

    # step 9
    Case.step('Run dmatest')
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        _, out, err = qemu.execute_vm_cmd(vm_name, './Guest_Mdev_Randomize_DSA_Conf.sh -x -i 1000 -j 10',
                                          timeout=10 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
    else:
        qemu.execute_vm_cmd(vm_name, 'rpm -ivh *.rpm --force --nodeps', timeout=10 * 60, cwd=KERNEL_INTERNAL_PATH_L)
        _, out, err = qemu.execute_vm_cmd(vm_name, './Guest_Mdev_Randomize_DSA_Conf.sh -i 1000 -j 10',
                                          timeout=10 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
    check_error(err)
    line_list = out.strip().split('\n')
    total_thread = 0
    threads_passed = 0
    for line in line_list:
        if 'Total Threads' in line:
            word_list0 = line.split(' ')
            total_thread = word_list0[2]
        if 'Threads Passed' in line:
            word_list1 = line.split(' ')
            threads_passed = word_list1[2]
    if total_thread != threads_passed:
        logger.error('dmatest fail')
        raise Exception('dmatest fail')

    # step 10
    Case.step('check dmesg log and close vm')
    _, out, err = qemu.execute_vm_cmd(vm_name, 'dmesg', timeout=10*60)
    check_error(err)
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        acce.modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', False)
    else:
        acce.modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on no5lvl', False)
    _, out, err = qemu.execute_vm_cmd(vm_name, 'shutdown now', timeout=10*60)
    qemu.kill_vm(vm_name)

    # step 11
    Case.step('Disable work-queues and MDEV devices')
    acce.disable_device_conf(cpu_num*acce.dsa_device_num, 'DSA')
    _, out, err = sut.execute_shell_cmd('dmesg', timeout=10*60)
    check_error(err)

    # Step 12 - Uninstall accel config tool
    Case.step('Uninstall accel config tool')
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        sut.execute_shell_cmd('make uninstall', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        sut.execute_shell_cmd('make clean', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        sut.execute_shell_cmd('make distclean', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', False)
    else:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl', False)

    acce.check_python_environment()


def clean_up(sut):
    from src.lib.toolkit.steps_lib import cleanup
    # cleanup.to_s5(sut)


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
