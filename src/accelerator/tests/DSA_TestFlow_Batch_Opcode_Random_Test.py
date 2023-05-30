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

    # Prepare steps - call predefined steps
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    acce.rpm_install()
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_dsa_2g2uuser1_bhs_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.init_bashrc()
    acce.kernel_header_devel()

    # Step 1 - Configure Linux Kernel boot parameters and install accel-config tool
    Case.step('Configure Linux Kernel boot parameters and install accel-config tool')
    acce.check_acce_device_status('dsa')
    acce.accel_config_install()

    # Step 2 -dsa_test on random number of work-queues
    Case.step('dsa_test on random number of work-queues ')
    out = acce.acce_random_test('Setup_Randomize_DSA_Conf.sh -c -F 1')
    acce.device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -b', '3')
    device_num = acce.check_enabled_device_num(out)
    acce.check_keyword([f'enabled {device_num} device(s) out of {device_num}'], out, 'setup all DSA config fail')
    dsa_opcode_list = [0, 3, 4, 5, 6, 9]
    for i in dsa_opcode_list:
        acce.device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -b', i)
    acce.disable_device_conf(device_num, 'DSA')

    # Step 3 -run dmatest on all work-queues
    Case.step('run dmatest on all work-queues')
    out = acce.acce_random_test('Setup_Randomize_DSA_Conf.sh -au -F 1')
    acce.device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -b', '3')
    device_num = acce.check_enabled_device_num(out)
    acce.check_keyword([f'enabled {device_num} device(s) out of {device_num}'], out, 'setup all DSA config fail')
    acce.dsa_opcode_list = [0, 3, 4, 5, 6, 9]
    for i in acce.dsa_opcode_list:
        acce.device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -b', i)
    acce.disable_device_conf(device_num, 'DSA')

    # Step 4 - check dmesg and Uninstall accel config tool
    sut.execute_shell_cmd('rm -rf /root/dmesg.log', timeout=60)
    sut.execute_shell_cmd('dmesg | tee /root/dmesg.log', timeout=60)
    sut.download_to_local(remotepath='/root/dmesg.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    ret, out, err = sut.execute_shell_cmd('dmesg|grep -i "error"', timeout=60)
    ignore_list = ['Error Record', 'error code -5', 'error -14', 'error -2']
    line_list = out.strip().split('\n')
    for line in line_list:
        ignore_flag = 0
        for i in range(len(ignore_list)):
            if ignore_list[i] in line:
                ignore_flag = 1
        if ('Error' in line or 'error' in line) and not ignore_flag:
            logger.error('dmesg show error')
            raise Exception('dmesg show error')

    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        sut.execute_shell_cmd('make uninstall', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        sut.execute_shell_cmd('make clean', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        sut.execute_shell_cmd('make distclean', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        acce.modify_kernel_grub("intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce", False)
    else:
        acce.modify_kernel_grub("intel_iommu=on,sm_on,iova_sl", False)
    


    acce.check_python_environment()


def clean_up(sut):
    pass
    # if Result.returncode != 0:
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
    # sut = get_default_sut()
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
