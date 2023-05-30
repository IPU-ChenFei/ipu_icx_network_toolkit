# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *


CASE_DESC = [
    'Configure Linux Kernel boot parameters and install accel-config tool',
    'Run IAX PCIE Remove rescan',
    'check logs and Uninstall accel config tool'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    # Prepare steps - call predefined steps
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_iax_stability_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.init_bashrc()
    acce.rpm_install()
    acce.kernel_header_devel()

    # Step 1 - Configure Linux Kernel boot parameters and install accel-config tool
    Case.step('Configure Linux Kernel boot parameters and install accel-config tool')
    acce.check_acce_device_status('iax')
    acce.accel_config_install()


    # Step 2 - Run IAX PCIE Remove rescan
    sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.execute_shell_cmd('unzip *.zip', timeout=5 * 60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    ret, out, _ = sut.execute_shell_cmd('./pci_remove_rescan.sh -d iax -n 10', cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}accel-random-config-and-test-main/accelerator_reset', timeout=1800)
    Case.expect('Run IAX PCIE Rescan successfully', ret == 0)

    # Step 3 - check logs and Uninstall accel config tool
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
