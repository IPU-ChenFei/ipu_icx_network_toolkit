# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *
#

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
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_iax_stability_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.init_bashrc()
    acce.rpm_install()
    acce.kernel_header_devel()
    sut.execute_shell_cmd('rm -rf /platform_rebooter/logs/platform_rebooter.log', timeout=60)
    sut.execute_shell_cmd('rm -rf /platform_rebooter/logs/mce.log', timeout=60)
    sut.execute_shell_cmd('rm -rf /platform_rebooter/logs/idxd.log', timeout=60)
    sut.execute_shell_cmd('rm -rf /platform_rebooter/logs/dmesg.log', timeout=60)


    # Step 1 - Configure Linux Kernel boot parameters and install accel-config tool
    Case.step('Configure Linux Kernel boot parameters and install accel-config tool')
    acce.check_acce_device_status('iax')
    acce.accel_config_install()

    # Step 2 - accel-config check
    Case.step('accel-config check')
    _, out, err = sut.execute_shell_cmd('accel-config list -i', timeout=60)
    acce.check_keyword(['iax'], out, 'Not detected Iax device')

    # Step 3 - Change grub file and install ipmi tool
    Case.step('Change grub file and install ipmi tool')
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', False)
    else:
        acce.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl', False)
    sut.execute_shell_cmd('yum -y install ipmitool', timeout=10*60)

    # Step 4 - Run IAX WarmBoot cycle
    Case.step('Run IAX WarmBoot cycle')
    sut.execute_shell_cmd('rm -rf /root/iax*.log', timeout=60)
    sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.execute_shell_cmd('unzip *.zip', timeout=5*60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
    sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_IAX_WB_PATH_L)
    sut.upload_to_remote(localpath=IAX_WB_H, remotepath=IAX_WB_PATH_L)
    ret, out, err = sut.execute_shell_cmd(f'python3 iax_wb.py iax_wb', timeout=10*60, cwd=IAX_WB_PATH_L)
    Case.expect("run iax wb cycle no error", ret == 0)
    Case.sleep(70)
    Case.wait_and_expect(f'SUT in OS', 100*60, sut.check_system_in_os)
    sut.download_to_local(f'/root/iax_cycle.log', os.path.join(LOG_PATH, 'Logs'))
    sut.download_to_local(f'/root/iax_wb.log', os.path.join(LOG_PATH, 'Logs'))

    # Step 5 - Check IAX WarmBoot log
    Case.step('Check IAX WarmBoot log')
    sut.download_to_local(remotepath='/platform_rebooter/logs/platform_rebooter.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    sut.download_to_local(remotepath='/platform_rebooter/logs/mce.log',localpath=os.path.join(LOG_PATH, 'Logs'))
    sut.download_to_local(remotepath='/platform_rebooter/logs/idxd.log',localpath=os.path.join(LOG_PATH, 'Logs'))
    sut.download_to_local(remotepath='/platform_rebooter/logs/dmesg.log',localpath=os.path.join(LOG_PATH, 'Logs'))
    ret, out, err = sut.execute_shell_cmd('cat platform_rebooter.log |grep -i "error"|wc -l', timeout=60, cwd='/platform_rebooter/logs/')
    Case.expect("platform_rebooter no error", int(out) == 0)
    ret, out, err = sut.execute_shell_cmd('cat idxd.log |grep -i "error"|wc -l', timeout=60, cwd='/platform_rebooter/logs/')
    Case.expect("idxd no error", int(out) == 0)
    ret, out, err = sut.execute_shell_cmd('cat dmesg.log |grep -i "error"', timeout=60, cwd='/platform_rebooter/logs/')
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
    ret, out, err = sut.execute_shell_cmd('cat mce.log | grep -i "error"|wc -l', timeout=60, cwd='/platform_rebooter/logs/')
    Case.expect("mce no error", int(out) == 0)

    # Step 6 - Uninstall accel config tool
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
