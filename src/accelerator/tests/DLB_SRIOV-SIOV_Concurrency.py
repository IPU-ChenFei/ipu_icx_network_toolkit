# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [

]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    qemu = RichHypervisor(sut)

    # Prepare steps - Enable VT-d in BIOS and install rpm package
    Case.prepare('boot to OS and enable VT-d  in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30 * 60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10 * 60, cwd='/home/')
    # sut.execute_shell_cmd('mv *.img.xz centos_basic.qcow2', timeout=10 * 60, cwd='/home/')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

    # Step 2 - Add function to grub file and clear abort log
    Case.step('Add function to grub file and clear abort log')
    acce.modify_kernel_grub('intel_iommu=on,sm_on iommu=on no5lvl', False)
    acce.modify_kernel_grub('intel_iommu=on,sm_on iommu=on', True)
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

    # Step 4 - Install DLB driver and check DLB device status
    Case.step('Install DLB driver and check DLB device status')
    acce.dlb_install(False)
    acce.check_acce_device_status('dlb')
    acce.create_dlb_mdev(0)

    #create VF
    def choose_dlb_device(num):
        Case.step('Unbind QAT PF 0 and open vm')
        dlb_dev_id = acce.get_dlb_dev_id_list(num, 1)
        sut.execute_shell_cmd('modprobe vfio')
        sut.execute_shell_cmd('modprobe vfio-pci')
        sut.execute_shell_cmd(f'echo 1 > /sys/class/dlb2/dlb{num}/device/sriov_numvfs')
        acce.unbind_device(f'dlb_{num}_1')
        return dlb_dev_id

    dlb_dev_id = choose_dlb_device(1)

    # Step 5 - Get device path
    Case.step('Get device path')
    def get_dev_path(sut):
        dev_dir = f'/sys/bus/mdev/devices/'
        std_out = sut.execute_shell_cmd(f'ls {dev_dir} | grep -')[1]
        dev_path = f'{dev_dir}/{std_out.strip()}'
        return dev_path
    dev_path = get_dev_path(sut)

    def os_kernel():
        ker_ver = acce.kernel_version()
        if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
            qemu_cmd = 'qemu-system-x86_64'
        else:
            qemu_cmd = '/usr/libexec/qemu-kvm'
        return qemu_cmd

    def execute_cmd(qemu_cmd):
        ker_ver = acce.kernel_version()
        if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
            exec_cmd = f'{qemu_cmd} -name {vm_name} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host -drive format=raw,file=/home/{vm_name}.qcow2 -bios /home/OVMF.fd  -device vfio-pci,sysfsdev={dev_path} -device vfio-pci,host={dlb_dev_id[0]} -smp 16 -serial mon:stdio -fsdev local,security_model=none,id=fsdev0,path=/home -device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=""modern"",device-iotlb=on,aw-bits=48 -nographic -nic user,hostfwd=tcp::2222-:22'
        else:
            exec_cmd = f'{qemu_cmd} -name {vm_name} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host -drive format=raw,file=/home/{vm_name}.qcow2 -bios /home/OVMF.fd  -device vfio-pci,sysfsdev={dev_path} -device vfio-pci,host={dlb_dev_id[0]} -smp 16 -serial mon:stdio -nographic -nic user,hostfwd=tcp::2222-:22'
        return exec_cmd

    # Step 6 - create and start vm
    Case.step('create and start vm')
    vm_name = 'vm'
    qemu.create_vm_from_template(vm_name, file_name)
    qemu_cmd = os_kernel()
    exec_cmd = execute_cmd(qemu_cmd)
    sut.execute_shell_cmd_async(exec_cmd)
    remain_try_times = 200
    while not qemu.try_to_connect(vm_name) and remain_try_times > 0:
        logger.info(f'waiting for {vm_name} boot into os...')
        Case.sleep(3)
        remain_try_times -= 1
    qemu.execute_vm_cmd(vm_name, 'lspci')

    # Step 7 - Install rpm package and kernel packages
    Case.step('Install rpm package and kernel packages')
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    acce.kernel_header_devel_vm(qemu, vm_name)
    acce.rpm_install_vm(qemu, vm_name)

    # Step 8 - Install DLB driver and run ldb_traffic stress
    Case.step('Install DLB driver and run ldb_traffic stress')
    acce.check_device_in_vm(qemu, vm_name, 'dlb', 2)
    acce.dlb_install_vm(qemu, vm_name, False)
    _, out, err = qemu.execute_vm_cmd(vm_name, './ldb_traffic -n 1024', timeout=60,
                                      cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples/')
    acce.check_keyword(['Received 1024 events'], out, 'execute dlb stress fail')

    # Step 9 - Install DPDK driver and run dpdk test
    Case.step('Install DPDK driver and run dpdk test')
    acce.run_dpdk_vm(qemu, vm_name)
    _, out, err = qemu.execute_vm_cmd(vm_name,
                                           './dpdk-test-eventdev --vdev=dlb2_event -- --test=order_queue --plcores=3 --wlcore=4,5 --nb_flows=64 --nb_pkts=100000000',
                                      timeout=10 * 60, cwd=f'{DPDK_DRIVER_PATH_L}*/builddir/app/')
    acce.check_keyword(['Success'], out, 'run dpdk test eventdev fail')

    # Step 10 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)
    qemu.undefine_vm(vm_name, True)

    # Step 11 - Clear grub config
    Case.step('Clear grub config')
    acce.modify_kernel_grub('intel_iommu=on,sm_on iommu=on', False)


    

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
