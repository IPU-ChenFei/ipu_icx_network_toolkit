# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'Driver basic check and device state check',
    'accel-config install',
    'accel-config test'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    Case.prepare('boot to OS with bios knobs modified')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_dsa_commom_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.init_bashrc()
    acce.rpm_install()

    # step 1 - Driver basic check and device state check
    Case.step('Driver basic check and device state check')
    _, out, err = sut.execute_shell_cmd('lsmod | grep idxd', timeout=60)
    acce.check_keyword(['idxd_mdev', 'idxd'], out, 'Driver not install')
    _, out, err = sut.execute_shell_cmd('dmesg | grep idxd', timeout=60)
    Case.expect('dmesg show driver no errmsg', err == '')
    acce.check_acce_device_status('dsa')

    # Step 2 - accel-config install
    Case.step('accel-config install')
    acce.accel_config_install()

    # Step 2 - accel-config test
    Case.step('accel-config test')
    _, out, err = sut.execute_shell_cmd('accel-config test', timeout=10*60)
    acce.check_keyword('SUCCESS', out, 'Issue - accel-config test fail')


    

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
