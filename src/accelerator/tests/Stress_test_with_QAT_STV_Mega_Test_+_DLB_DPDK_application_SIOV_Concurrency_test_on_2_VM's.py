# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *
from src.virtualization.lib.virtualization import *


CASE_DESC = [

]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    qemu = RichHypervisor(sut)
    kvm = get_vmmanger(sut)
    qat_vm_name = 'vm'
    dlb_vm_name = 'vm_dlb'
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

    # Prepare steps - Enable VT-d in BIOS and install rpm package
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)



    # Step 2 - Add SIOV function to grub file and clear abort log
    Case.step('Add SIOV function to grub file and clear abort log')
    acce.modify_kernel_grub('intel_iommu=on,sm_on', True)
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
    acce.check_acce_device_status('qat')
    acce.qat_uninstall()
    acce.qat_install(True)
    acce.check_qat_service_status(True)

    # Step 5 - Modify QAT config file and show VQAT device
    Case.step('Modify QAT config file and show VQAT device')
    sut.execute_shell_cmd(f'sed -i "s/NumberCyInstances = 1/NumberCyInstances = 0/g" /etc/4xxx_dev0.conf',
                          timeout=60)
    sut.execute_shell_cmd(f'sed -i "s/NumberCyInstances = 3/NumberCyInstances = 0/g" /etc/4xxx_dev0.conf',
                                   timeout=60)
    sut.execute_shell_cmd(f'sed -i "s/NumberDcInstances = 2/NumberDcInstances = 0/g" /etc/4xxx_dev0.conf',
                                   timeout=60)
    sut.execute_shell_cmd(f'sed -i "s/NumberAdis = 0/NumberAdis = 64/g" /etc/4xxx_dev0.conf',
                          timeout=60)

    def qat_SRIOV_SIOV_Concurrency_service_stop_start():
        cpu_num = acce.get_cpu_num()
        _, out, err1 = sut.execute_shell_cmd('service qat_service stop', timeout=10 * 60)
        line_list = out.strip().split('\n')
        dev_num = 0
        for line in line_list:
            if 'Stopping device qat_dev' in line:
                dev_num += 1
        if dev_num != cpu_num * acce.qat_device_num * 16:
            logger.error('Not all QAT vf stopped')
            raise Exception('Not all QAT vf stopped')

        _, out, err = sut.execute_shell_cmd('service qat_service start', timeout=10 * 60)
        line_list = out.strip().split('\n')
        dev_num = 0
        for line in line_list:
            if 'state: up' in line:
                dev_num += 1
        if dev_num != ((cpu_num * acce.qat_device_num * 17)-16):
            logger.error('Not all QAT pf status show up')
            raise Exception('Not all QAT pf status show up')

    qat_SRIOV_SIOV_Concurrency_service_stop_start()

    _, out, err = sut.execute_shell_cmd('./build/vqat_ctl show', timeout=60, cwd=QAT_DRIVER_PATH_L)
    line_list = out.strip().split('BDF:')
    line_list.pop(0)
    sym_device_num = 0
    dc_device_num = 0
    for line in line_list:
        str_list = line.strip().split('\n')
        sym_name = str_list[1].strip().split(':')
        sym_num = int(sym_name[1].strip())
        if sym_num == 32:
            sym_device_num += 1
        dc_name = str_list[3].strip().split(':')
        dc_num = int(dc_name[1].strip())
        if dc_num == 32:
            dc_device_num += 1
    print(sym_device_num)
    print(dc_device_num)
    if sym_device_num != 1 and dc_device_num != 1:
        logger.error('Not first device get available sym and available dc value')
        raise Exception('Not first device get available sym and available dc value')
    sut.execute_shell_cmd('./build/vqat_ctl –help', timeout=60, cwd=QAT_DRIVER_PATH_L)


    # Step 6 - Set VQAT sym and dc
    Case.step('Set VQAT sym and dc')
    get_qat_dev_id_00 = acce.get_dev_id('qat', 0, 0)
    print(get_qat_dev_id_00)

    def get_device_uuid(out):
        device_uuid = ''
        line_list = out.strip().split('\n')
        for line in line_list:
            str_list = line.split(',')
            dev_name = str_list[1].split('=')
            device_uuid = dev_name[1].strip()
        return device_uuid

    qat_mdev_id_list = []

    for i in range(1,25):
        _, out, err = sut.execute_shell_cmd(f'./build/vqat_ctl create {get_qat_dev_id_00} sym', timeout=60, cwd=QAT_DRIVER_PATH_L)
        acce.check_keyword(['VQAT-sym created successfully'], out, 'VQAT-sym create fail')
        sym_uuid = get_device_uuid(out)
        print(sym_uuid)
        qat_mdev_id_list.append(sym_uuid)

    for i in range(1, 30):
        _, out, err = sut.execute_shell_cmd(f'./build/vqat_ctl create {get_qat_dev_id_00} dc', timeout=60, cwd=QAT_DRIVER_PATH_L)
        acce.check_keyword(['VQAT-dc created successfully'], out, 'VQAT-dc create fail')
        dc_uuid = get_device_uuid(out)
        print(dc_uuid)
        qat_mdev_id_list.append(dc_uuid)
    _, out, err = sut.execute_shell_cmd('./build/vqat_ctl show', timeout=60, cwd=QAT_DRIVER_PATH_L)
    sym_num = 0
    dc_num = 0
    line_list = out.strip().split('BDF:')
    for line in line_list:
        str_list = line.strip().split('\n')
        if str_list[0] == f'{get_qat_dev_id_00}':
            sym_name = str_list[1].strip().split(':')
            sym_num = int(sym_name[1].strip())
            dc_name = str_list[3].strip().split(':')
            dc_num = int(dc_name[1].strip())
    if sym_num != 8 and dc_num != 3:
        logger.error('VQAT set unsuccessful')
        raise Exception('VQAT set unsuccessful')



    #Step 7 - Install DLB driver and check DLB device status
    Case.step('Install DLB driver and check DLB device status')
    acce.dlb_install(False)
    acce.check_acce_device_status('dlb')
    sut.execute_shell_cmd('modprobe vfio', timeout=60)
    sut.execute_shell_cmd('modprobe vfio-pci', timeout=60)
    sut.execute_shell_cmd('modprobe mdev', timeout=60)
    acce.create_dlb_mdev(1)

    # Step 8 - Get DLB mdev device path adm qemu cmd
    Case.step('Get device path')
    def get_dev_path(sut):
        dev_dir = f'/sys/bus/mdev/devices/'
        std_out = sut.execute_shell_cmd(f'cat /root/uuidgen.txt')[1]
        dev_path = f'{dev_dir}{std_out.strip()}'
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
            exec_cmd = f'{qemu_cmd} -name {dlb_vm_name} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host -drive format=raw,file=/home/{dlb_vm_name}.qcow2 -bios /home/OVMF.fd  -device vfio-pci,sysfsdev={dev_path} -smp 16 -serial mon:stdio -fsdev local,security_model=none,id=fsdev0,path=/home -device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=""modern"",device-iotlb=on,aw-bits=48 -nographic -nic user,hostfwd=tcp::2222-:22'
        else:
            exec_cmd = f'{qemu_cmd} -name {dlb_vm_name} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host -drive format=raw,file=/home/{dlb_vm_name}.qcow2 -bios /home/OVMF.fd  -device vfio-pci,sysfsdev={dev_path} -smp 16 -serial mon:stdio -nographic -nic user,hostfwd=tcp::2222-:22'
        return exec_cmd


    # Step 9- create and start dlb vm
    Case.step('create and start dlb vm')
    qemu.create_vm_from_template(dlb_vm_name, file_name)
    qemu_cmd = os_kernel()
    exec_cmd = execute_cmd(qemu_cmd)
    sut.execute_shell_cmd_async(exec_cmd)
    remain_try_times = 200
    while not qemu.try_to_connect(dlb_vm_name) and remain_try_times > 0:
        logger.info(f'waiting for {dlb_vm_name} boot into os...')
        Case.sleep(3)
        remain_try_times -= 1
    qemu.execute_vm_cmd(dlb_vm_name, 'lspci')

    # Step 10 - create and start qat vm

    Case.step('creat and start qat vm')
    is_vm_exist = kvm.is_vm_exist(qat_vm_name)
    if is_vm_exist:
        kvm.undefine_vm(qat_vm_name)
    kvm.create_vm_from_template(qat_vm_name, file_name, ram_mb=16384, disk_dir=f'{IMAGE_PATH_L}')
    acce.attach_mdev_to_vm(kvm, qat_vm_name, qat_mdev_id_list)
    sut.execute_shell_cmd(f'virsh setvcpus {qat_vm_name} --maximum 4 --config', timeout=120)
    sut.execute_shell_cmd(f'virsh setvcpus {qat_vm_name} --count 4 --config', timeout=120)
    kvm.start_vm(qat_vm_name)


    # Step 11 - Install rpm package and kernel packages in DLB vm
    Case.step('Install rpm package and kernel packages')
    qemu.execute_vm_cmd(dlb_vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    kvm.execute_vm_cmd(qat_vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    acce.kernel_header_devel_vm(qemu, dlb_vm_name)
    acce.kvm_kernel_header_devel_vm(kvm, qat_vm_name)
    acce.rpm_install_vm(qemu, dlb_vm_name)
    acce.kvm_rpm_install_vm(kvm, qat_vm_name)


    # Step 12 - Install QAT driver and Mega on qat vm
    Case.step('Install QAT driver and run qat sanmple code stress')
    acce.kvm_qat_uninstall_vm(kvm, qat_vm_name)
    acce.kvm_qat_install_vm(kvm, qat_vm_name, './configure --enable-icp-sriov=guest',  enable_siov=True)
    acce.kvm_qat_vm_mega_install(kvm, qat_vm_name)

    # Step 13 - Install DLB driver and DPDK on dlb vm
    Case.step('Install DLB driver and DPDK')
    acce.check_device_in_vm(qemu, dlb_vm_name, 'dlb', 1)
    acce.dlb_install_vm(qemu, dlb_vm_name, True)
    Case.step('Install DPDK driver and run dpdk test')
    acce.run_dpdk_vm(qemu, dlb_vm_name)

    # Step 14 - Run mega and DPDK tests.
    sut.execute_shell_cmd('rm -f mega.log', timeout=5 * 60, cwd=f'{MEGA_SCRIPT_PATH_L}')
    kvm.execute_vm_cmd_async(qat_vm_name, f'python3 mega_script.py run_testcli > ignore.log', cwd=MEGA_SCRIPT_PATH_L)
    sut.execute_shell_cmd('rm -f dpdk.log', timeout=5 * 60, cwd=f'{DPDK_DRIVER_PATH_L}')
    qemu.execute_vm_cmd(dlb_vm_name, f"./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64 > {DPDK_DRIVER_PATH_L}dpdk.log", timeout=10 * 60, cwd=f'{DPDK_DRIVER_PATH_L}*/builddir/app/')
    #check dpdk log
    qemu.download_from_vm(dlb_vm_name, f'{DPDK_DRIVER_PATH_L}dpdk.log', f'{DPDK_DRIVER_PATH_L}dpdk.log')
    sut.download_to_local(remotepath=f'{DPDK_DRIVER_PATH_L}dpdk.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    _, out, err = sut.execute_shell_cmd('cat dpdk.log', timeout=5 * 60, cwd=f'{DPDK_DRIVER_PATH_L}')
    acce.check_keyword(['Success'], out, 'run dpdk test eventdev fail')

   # check mega log
    kvm.download_from_vm(qat_vm_name, f'{MEGA_SCRIPT_PATH_L}mega.log', f'{MEGA_SCRIPT_PATH_L}mega.log')
    sut.download_to_local(remotepath=f'{MEGA_SCRIPT_PATH_L}mega.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    _, out, err = sut.execute_shell_cmd(f'cat {MEGA_SCRIPT_PATH_L}mega.log', timeout=60)
    mega_list = out.strip().split('\n')
    tms_pass_num = 0
    for line in mega_list:
        if 'TMS PASSED' in line:
            tms_pass_num += 1
    if tms_pass_num != 7:
        logger.error(err)
        raise Exception(err)




    #Step 15 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    rcode, out, err = kvm.execute_vm_cmd(qat_vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    rcode, out, err = qemu.execute_vm_cmd(dlb_vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    kvm.shutdown_vm(qat_vm_name)
    kvm.undefine_vm(qat_vm_name)
    qemu.shutdown_vm(dlb_vm_name)
    # qemu.kill_vm(dlb_vm_name)
    qemu.undefine_vm(dlb_vm_name, True)


    # Step 16 - Clear grub config
    Case.step('Clear grub config')
    acce.modify_kernel_grub('intel_iommu=on,sm_on', False)
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
