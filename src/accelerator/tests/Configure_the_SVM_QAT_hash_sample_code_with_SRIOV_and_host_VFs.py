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
    Case.prepare('boot to OS and enable VT-d  in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1
    Case.step('Add SRIOV function to grub file and clear abort log')
    acce.modify_kernel_grub('intel_iommu=on,sm_on', True)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # Step 2
    Case.step('Check QAT device status and install QAT driver')
    acce.check_acce_device_status('qat')
    acce.qat_uninstall()
    acce.qat_install(True)
    acce.check_qat_service_status(True)
    
    # Step 3
    Case.step('Check dev_cfg of the VF to see if SVM is enabled')
    _, out, err = sut.execute_shell_cmd('cat /sys/kernel/debug/qat_4xxx_0000\:6b\:00.0/dev_cfg | grep -i svm', timeout=60)
    acce.check_keyword('SVMEnabled = 1', out, 'SVM can not enabled successfully')

    # Step 4
    Case.step('run hash_sample')
    PATH = f'{QAT_DRIVER_PATH_L}/quickassist/lookaside/access_layer/src/sample_code/functional'
    acce.add_environment_to_file('ICP_ROOT', 'export ICP_ROOT=/home/BKCPkg/domains/accelerator/QAT/')
    sut.execute_shell_cmd('source /root/.bashrc', timeout=60)
    ret, out, _ = sut.execute_shell_cmd('make all', timeout=60*10, cwd=PATH)
    ret, out, _ = sut.execute_shell_cmd('./hash_sample', timeout=60 * 10, cwd=f'{PATH}/build')
    acce.check_keyword('Hash Sample Code App finished', out, 'hash_sample application test fail')

    # Step 5
    Case.step('clear grub config')
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
