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
    Case.prepare('boot to OS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to(sut, sut.default_os)
    # cpu_num = acce.get_cpu_num_esxi()
    cpu_num = int(sut.cfg['defaults']['socket_num'])

    # step 1 - Check DLB device in VMware OS
    Case.step('Check DLB device in VMware OS')
    sut.execute_shell_cmd(f'esxcfg-module -u dlb', timeout=60)
    sut.execute_shell_cmd(f'esxcli software component remove -n Intel-dlb', timeout=60)
    acce.check_acce_device_esxi('dlb', cpu_num)

    # step 2 - Install DLB driver
    Case.step('Install DLB driver')
    acce.dlb_driver_install_esxi()
    acce.check_acce_device_esxi('dlb', cpu_num, True)

    # step 3 - Uninstall DLB driver
    Case.step('Uninstall DLB driver')
    acce.uninstall_driver_esxi('dlb')
    acce.check_acce_device_esxi('dlb', cpu_num)


    

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
