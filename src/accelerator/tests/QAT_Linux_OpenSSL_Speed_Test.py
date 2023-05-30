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
    boot_to(sut, sut.default_os)
    ifwi_ver = acce.get_ifwi_version()
    if ifwi_ver >= acce.IFWI_VERSION:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_vtd_common_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_vtd_common_xmlcli'))
    else:
        set_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.add_environment_to_file('http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
    acce.add_environment_to_file('HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
    acce.add_environment_to_file('https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
    acce.add_environment_to_file('HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
    acce.add_environment_to_file('no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
    sut.execute_shell_cmd(f'yum -y install zlib-devel.x86_64 yasm systemd-devel boost-devel.x86_64 openssl-devel libnl3-devel gcc gcc-c++ libgudev.x86_64 libgudev-devel.x86_64 systemd*', timeout=60000)
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - Check QAT device
    Case.step('Check QAT device')
    acce.check_acce_device_status('qat')

    # Step 2 - QAT driver install and run qat sample
    Case.step('QAT driver install and run qat sample')
    acce.qat_uninstall()
    acce.qat_install(False)
    acce.run_qat_sample_code('')

    # Step 3 - Modify qat config file
    Case.step('Modify qat config file')
    acce.modify_qat_config_file('shim')
    acce.check_qat_service_status()

    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        acce.openssl_install()

    # Step 4 - Install QAT engine
    Case.step('Install QAT engine')
    acce.qat_engine_install()
    acce.qat_service_restart()
    acce.check_qat_service_status()

    # Step 5 - Run QAT sym test
    Case.step('Run QAT sym test')
    acce.run_openssl(False)

    # Step 6 - Run QAT asym test
    Case.step('Run QAT asym test')
    acce.run_openssl(True)

    # Step 7 - Clear test environment
    Case.step('Clear test environment')
    acce.qat_engine_uninstall()
    acce.delete_environment('OPENSSL_ENGINES')
    acce.delete_environment('LD_LIBRARY_PATH')


    

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
