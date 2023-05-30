import set_toolkit_src_root
from src.accelerator.lib import *


CASE_DESC = [
    'Check DLB device in VMware OS',
    'Install DLB driver',
    'Check DLB device in VMware OS'
    'Uninstall DLB driver'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    # Prepare steps - call predefined steps
    Case.prepare('boot to OS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to(sut, sut.default_os)

    # step 1 - Check DLB device in VMware OS
    Case.step('Check DLB device in VMware OS')
    # acce.uninstall_driver_esxi('dlb')
    _, out, err = sut.execute_shell_cmd("esxcli system settings kernel list | grep iovPasidMode | awk '{print $4}'", timeout=60)
    if 'TRUE\n' not in out:
        sut.execute_shell_cmd('esxcli system settings kernel set --setting=iovPasidMode --value=TRUE', timeout=60)
        my_os.warm_reset_cycle_step(sut)
    acce.check_acce_device_esxi('dlb', 2, False)

    # step 2 - Install DLB driver
    Case.step('Install DLB driver')
    acce.dlb_driver_install_esxi(True)

    # step 3 - Check DLB device in VMware OS
    Case.step('Check DLB device in VMware OS')
    acce.check_acce_device_esxi('dlb', 2, True)

    # step 4 - Uninstall DLB driver
    Case.step('Uninstall DLB driver')
    acce.uninstall_driver_esxi('dlb')



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
        # clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
