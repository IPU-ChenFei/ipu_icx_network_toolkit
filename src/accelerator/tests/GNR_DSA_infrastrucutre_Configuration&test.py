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
    acce.init_bashrc()
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_dsa_2g2uuser1_egs_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.rpm_install()
    acce.kernel_header_devel()


    # Step 1 - Configure Linux Kernel boot parameters and install accel-config tool
    Case.step('Configure Linux Kernel boot parameters and install accel-config tool')
    acce.accel_config_install()

    # Step 2 - Check DSA device
    Case.step('Check DSA device')
    acce.check_acce_device_status('dsa')
    _, out, err = sut.execute_shell_cmd('lsmod | grep idxd', timeout=60)
    acce.check_keyword(['idxd_mdev', 'idxd', 'vfio_pci', 'irqbypass'], out, 'DSA driver check fail')
    _, out, err = sut.execute_shell_cmd('dmesg | grep idxd', timeout=60)
    # acce.check_keyword(['vdcm_vidxd_create, idxd migration region init successfully'], out, 'idxd migration region init unsuccessful')
    if 'error' in out:
        logger.error('dmesg show error')
        raise Exception('dmesg show error')
    cpu_num = acce.get_cpu_num()
    line_list = out.strip().split('\n')
    dsa_device_num = 0
    for line in line_list:
        if 'enabling device' in line:
            dsa_device_num += 1
    if dsa_device_num != cpu_num*acce.dsa_device_num*2:
        logger.error('Not all idxd device detected')
        raise Exception('Not all idxd device detected')

    # Step 3 - Check DSA file
    Case.step('Check DSA file')
    _, out, err = sut.execute_shell_cmd('ls /sys/bus/dsa', timeout=60)
    acce.check_keyword(['devices', 'drivers', 'drivers_autoprobe', 'drivers_probe', 'uevent'], out, 'DSA file check fail')
    _, out, err = sut.execute_shell_cmd('ls /sys/bus/dsa/devices', timeout=5*60)
    acce.check_keyword(['dsa'], out, 'Not all DSA device are detected')

    # Step 4 - Execute accel-config test
    Case.step('Execute accel-config test')
    my_os.warm_reset_cycle_step(sut, timeout=3600)
    sut.execute_shell_cmd('accel-config test > accel-config-test.log', timeout=60)
    _, out, err = sut.execute_shell_cmd('cat accel-config-test.log', timeout=60, cwd='/root')
    acce.check_keyword(['SUCCESS'], out, 'accel-config test fail')

    # Step 5 - Config 2 group 2 queues user 1
    Case.step('Config 2 group 2 queues user 1')
    acce.dsa_wq_2g2q_user_1(0)


    def dmesg_check():
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

    # Step 6 - cycling run setup all DSA config
    Case.step('cycling run setup all DSA config ')
    for i in range(3):
        out = acce.acce_random_test('Setup_Randomize_DSA_Conf.sh -a')
        device_num = acce.check_enabled_device_num(out)
        dmesg_check()
        acce.accel_config_check(device_num, 'dsa')
        acce.disable_device_conf(device_num, 'DSA')
        dmesg_check()

    # Step 7 - Configure one user WQ for each available DSA
    Case.step('Configure one user WQ for each available DSA')
    out = acce.acce_random_test('Setup_Randomize_DSA_Conf.sh -au')
    device_num = acce.check_enabled_device_num(out)


    # Step 8 - Run DSA config stress
    Case.step('Run DSA config stress')
    dsa_opcode_list = [2, 3, 4, 5, 6, 9]
    for i in dsa_opcode_list:
        acce.device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -o', i)
        dmesg_check()

    # Step 9 - Check dmesg log and disable dsa config
    Case.step('Check dmesg log and disable dsa config')
    acce.disable_device_conf(device_num, 'DSA')


    # Step 10 - dmatest on random number of work-queues
    Case.step('dmatest on random number of work-queues')
    out = acce.acce_random_test('Setup_Randomize_DSA_Conf.sh -c')
    device_num = acce.check_enabled_device_num(out)


    # Step 11 -run dmatest
    Case.step('run dmatest')
    acce.dmatest_check('DSA')
    acce.disable_device_conf(device_num, 'DSA')
    dmesg_check()

    # Step 12 -run dmatest on all work-queues
    Case.step('run dmatest on all work-queues')
    out = acce.acce_random_test('Setup_Randomize_DSA_Conf.sh -ka')
    device_num = acce.check_enabled_device_num(out)

    # Step 13 - dmatest check
    Case.step('dmatest check')
    acce.dmatest_check('DSA')
    acce.disable_device_conf(device_num, 'DSA')
    dmesg_check()

    # Step 14 - Uninstall accel config tool
    Case.step('Uninstall accel config tool')
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        sut.execute_shell_cmd('make uninstall', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        sut.execute_shell_cmd('make clean', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
        sut.execute_shell_cmd('make distclean', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')

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
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
