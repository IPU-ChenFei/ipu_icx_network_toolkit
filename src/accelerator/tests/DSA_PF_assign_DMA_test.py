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

    # Prepare steps - Enable VT-d in BIOS and install rpm package
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_dsa_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30 * 60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10 * 60, cwd='/home/')
    # sut.execute_shell_cmd('cp centos_basic.qcow2 centos.qcow2', timeout=10 * 60, cwd='/home/')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    sut.upload_to_remote(localpath=DSA_H, remotepath=DSA_PATH_L)
    sut.upload_to_remote(localpath=IDXD_KTEST_MASTER_H, remotepath=IDXD_KTEST_MASTER_PATH_L)
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

    # Step 2 - Add function to grub file and clear abort log
    Case.step('Add function to grub file and clear abort log')
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce no5lvl', True)
    else:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl no5lvl', True)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # Step 3 - Install sut environments
    Case.step('Install sut environments')
    sut.execute_shell_cmd('python -m pip install --upgrade pip --proxy=http://child-prc.intel.com:913', timeout=120)
    sut.execute_shell_cmd('python -m pip install --upgrade paramiko --proxy=http://child-prc.intel.com:913', timeout=180)
    sut.execute_shell_cmd(f'mkdir {SRC_SCRIPT_PATH_L}')
    sut.execute_shell_cmd(f'rm -rf {SRC_SCRIPT_PATH_L}*')
    sut.upload_to_remote(localpath=SRC_SCRIPT_H, remotepath=SRC_SCRIPT_PATH_L)
    sut.execute_shell_cmd('unzip *', timeout=5 * 60, cwd=f'{SRC_SCRIPT_PATH_L}')

    # Step 4 - Check QAT device status and install QAT driver
    Case.step('Check QAT device status and install QAT driver')
    sut.execute_shell_cmd('modprobe vfio', timeout=60)
    sut.execute_shell_cmd('modprobe vfio-pci', timeout=60)
    dsa_dev_id = acce.get_dev_id('dsa', 0, 0)
    acce.unbind_device('dsa_0_0')

    # Step 5 - create and start vm
    Case.step('create and start vm')
    vm_name = 'vm'
    qemu.kill_vm(vm_name)
    qemu.register_vm(vm_name, file_name, add_by_host=False, is_sriov=False)
    # qemu.create_vm_from_template(vm_name, file_name, add_by_host=False, is_sriov=False)
    qemu.attach_acce_dev_to_vm(vm_name, [dsa_dev_id])
    qemu.start_vm(vm_name)
    ret, _ , _ = qemu.execute_vm_cmd(vm_name, f"yum groupinstall -y \'Development Tools\' --allowerasing", timeout=10*60)
    Case.expect('yum install Development Tools pass', ret == 0)
    qemu.execute_vm_cmd(vm_name, 'yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools', timeout=10*60)
    qemu.execute_vm_cmd(vm_name, 'yum install -y asciidoc xmlto libuuid-devel json-c-devel kmod-devel libudev-devel', timeout=10*60)

    # Step 6 - Install rpm package and kernel packages
    Case.step('Install rpm package and kernel packages')
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    acce.kernel_header_devel_vm(qemu, vm_name)
    acce.rpm_install_vm(qemu, vm_name)

    # Step 7 - detect DSA device and add SIOV function to vm
    Case.step('detect DSA device and add SIOV function to vm')
    acce.check_device_in_vm(qemu, vm_name, 'dsa', 0)
    acce.modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on iommu=on no5lvl', True)
    time.sleep(60)

    # Step 8 - copy idxd ktest master and DSA tool to vm
    def tool_upload(qemu, vm_name):
        Case.step('copy idxd ktest master and DSA tool to vm')
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {IDXD_KTEST_MASTER_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {IDXD_KTEST_MASTER_PATH_L}*', timeout=60)
        sut_file_dir = f'{IDXD_KTEST_MASTER_PATH_L}{IDXD_KTEST_MASTER_NAME}'
        vm_file_dir = f'{IDXD_KTEST_MASTER_PATH_L}{IDXD_KTEST_MASTER_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)

        qemu.execute_vm_cmd(vm_name, f'mkdir -p {DSA_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {DSA_PATH_L}*', timeout=60)
        sut_file_dir1 = f'{DSA_PATH_L}{DSA_ACCEL_CONFIG_NAME}'
        vm_file_dir1 = f'{DSA_PATH_L}{DSA_ACCEL_CONFIG_NAME}'
        sut.upload_to_remote(localpath=DSA_H, remotepath=DSA_PATH_L)
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

    # Step 9 - Run idxd ktest in vm
    Case.step('Run idxd ktest in vm')
    qemu.execute_vm_cmd(vm_name, 'unzip *', timeout=60, cwd=f'{IDXD_KTEST_MASTER_PATH_L}')
    qemu.execute_vm_cmd(vm_name, 'rpm -ivh *.rpm --force --nodeps', timeout=10 * 60, cwd=KERNEL_INTERNAL_PATH_L)
    rcode, out, err = qemu.execute_vm_cmd(vm_name, './idxd_ktest.sh -d dsa -c 1 -t 1 -i 1000', timeout=10 * 60, cwd=f'{IDXD_KTEST_MASTER_PATH_L}*/')
    acce.check_keyword(['Test passed'], out, 'idxd ktest test fail')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, './idxd_ktest.sh -d dsa -c 1 -t 2 -i 1000', timeout=10 * 60,
                        cwd=f'{IDXD_KTEST_MASTER_PATH_L}*/')
    acce.check_keyword(['Test passed'], out, 'idxd ktest test fail')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, './idxd_ktest.sh -d dsa -c 1 -t 1 -i 100000', timeout=10 * 60,
                                          cwd=f'{IDXD_KTEST_MASTER_PATH_L}*/')
    acce.check_keyword(['Test passed'], out, 'idxd ktest test fail')

    # Step 10 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)

    # Step 11 - clear grub config
    Case.step('clear grub config')
    acce.modify_kernel_grub('intel_iommu=on,sm_on iommu=on no5lvl', False)


    

    acce.check_python_environment()


def clean_up(sut):
    pass
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)


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
