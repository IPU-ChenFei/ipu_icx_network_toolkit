import uuid
import time
# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *







CASE_DESC = [

]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    qemu = RichHypervisor(sut)

    # Prepare steps - Enable VT-d in BIOS and install rpm package
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy spr acce random tool and OVFM tool to SUT
    Case.step('copy spr acce random tool and OVFM tool to SUT')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=SPR_ACCE_RANDOM_CONFIG_PATH_L)

    # Step 2 - Add function to grub file and clear abort log
    Case.step('Add function to grub file and clear abort log')
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



    #step 4 Config wq and creat mdev
    def get_device_uuid(out):
        line_list = out.strip('\n').split(' ')
        device_uuid =line_list[4]
        return device_uuid

    def check_uuid4(test_uuid, version=4):
        print(test_uuid)
        uuid_version = uuid.UUID(test_uuid).version
        print(uuid_version)
        if uuid.UUID(test_uuid).version != version:
            logger.error('This is not a uuid')
            raise Exception('This is not a uuid')

    device_uuid_list = []
    sut.execute_shell_cmd('accel-config config-wq --group-id=0 --mode=shared -t 8 --wq-size=16 --type=mdev --driver-name=mdev --priority=10 dsa0/wq0.0 --name=guest', timeout=120)
    sut.execute_shell_cmd('accel-config config-engine dsa0/engine0.0 --group-id=0', timeout=120)
    sut.execute_shell_cmd('accel-config enable-device dsa0', timeout=120)
    sut.execute_shell_cmd('accel-config enable-wq dsa0/wq0.0', timeout=120)
    for i in range(0,2):
        _, out, err = sut.execute_shell_cmd('accel-config create-mdev dsa0 1swq', timeout=120)
        dsa_uuid = get_device_uuid(out)
        print(dsa_uuid)
        check_uuid4(dsa_uuid)
        device_uuid_list.append(dsa_uuid)




    # Step 5 - create and start vm
    Case.step('create and start vm')
    file_name = f'{IMAGE_PATH_L}{CLEAN_IMAGE_NAME}'
    qemu.create_rich_vm(2, file_name, add_by_host=False, is_sriov=False, is_uuid=True)
    qemu.attach_acce_dev_to_vm_grouply(device_uuid_list, 1)
    qemu.start_rich_vm()

    # Step 6 - install DSA tool in rich vm
    Case.step('Install rpm package , kernel packages AND accel-config tool')
    qemu.execute_rich_vm_cmd_parallel('abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    acce.modify_kernel_grub_rich_vm(qemu, 'intel_iommu=on,sm_on no5lvl', True)
    acce.rpm_install_rich_vm(qemu)
    acce.install_accel_config_rich_vm(qemu)

    # Step 7 - run dsa test
    qemu.execute_rich_vm_cmd_parallel('unzip *.zip', timeout=10 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}')
    exec_res = qemu.execute_rich_vm_cmd_parallel('accel-config config-wq --type=user --name="dmaengine" -d user  dsa0/wq0.0', timeout=10 * 60)
    for vm in exec_res:
        res = exec_res[vm][0]
        Case.expect('wq config pass', res == 0)
    exec_res1 = qemu.execute_rich_vm_cmd_parallel('accel-config enable-wq dsa0/wq0.0', timeout=10 * 60)
    for vm in exec_res1:
        out = exec_res1[vm][2]
        acce.check_keyword(['enabled 1 wq(s) out of 1'], out, 'wq enabled fail')
    exec_res2 = qemu.execute_rich_vm_cmd_parallel('./Setup_Randomize_DSA_Conf.sh  -o 0x3', timeout=10 * 60,
                        cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
    for vm in exec_res2:
        out = exec_res2[vm][1]
        acce.check_keyword(['1 of 1 work queues logged completion records'], out, 'DSA  test fail')

    # Step 8 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    exec_res3 = qemu.execute_rich_vm_cmd_parallel('abrt-cli list | grep mce|wc -l', timeout=60)
    for vm in exec_res3:
        out = exec_res3[vm][1]
        err = exec_res3[vm][2]
        if int(out) != 0:
            logger.error(err)
            raise Exception(err)

    # Step 9 - shutdown vm
    Case.step('shutdown vm')
    qemu.shutdown_rich_vm()
    qemu.undefine_rich_vm()

    # Step 10 - clear grub config
    Case.step('clear grub config')
    acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl no5lvl', False)
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
