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
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sgx_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    acce.kernel_header_devel()
    acce.rpm_install()

    # Step 1 - Check SGX value
    Case.step('Check SGX value')
    acce.sgx_msr_value_check()
    my_os.reset_to_uefi_shell(sut)
    acce.cpuid_check()
    UefiShell.exit_to_bios_menu(sut)
    sut.bios.bios_setup_continue_to_os()
    Case.wait_and_expect(f'system in os', 5 * 60, sut.check_system_in_os)


    # Step 2 - Check dlb device
    Case.step('Check dlb device')
    acce.check_acce_device_status('dlb')

    # Step 3 - DLB driver install and run dlb traffic test
    Case.step('DLB driver install and run dlb traffic test')
    acce.delete_environment('LD_LIBRARY_PATH')
    acce.dlb_install(True)
    _, out, err = sut.execute_shell_cmd('./ldb_traffic -n 1024', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples/')
    acce.check_keyword(['[tx_traffic()] Sent 1024 events', '[rx_traffic()] Received 1024 events'], out, 'Run DLB stress fail')
    acce.delete_environment('LD_LIBRARY_PATH')

    # Step 4 - Install sgx driver and run sgx hydra test
    Case.step('Install sgx driver and run sgx hydra test')
    acce.sgx_install_and_test()
    acce.sgx_sampleenclave_test()

    # Step 5 - Clear environments
    Case.step('Clear environments')
    acce.delete_environment('LD_LIBRARY_PATH')
    acce.delete_environment('source')




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
