import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'check the working of  DLB/HQM - DPDK Event-dev test application on Host'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    Case.prepare('boot to OS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to(sut, sut.default_os)
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()

    # step 1 - install DLB driver
    Case.step('install DLB driver')
    acce.dlb_install(True)

    # Step 2 - Download and  Extract DPDK driver
    Case.step('Download and  Extract DPDK driver')
    acce.run_dpdk()
    dpdk_command = './dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue' \
                   ' --plcores=1 --wlcore=2,3 --nb_flows=64'
    dpdk_path = f'{DPDK_DRIVER_PATH_L}*/builddir/app'
    _, out, err = sut.execute_shell_cmd("{}".format(dpdk_command), timeout=60, cwd=dpdk_path)
    acce.check_keyword(['Success'], out, 'run dpdk test eventdev fail')

    # Step 3 - uninstall DLB driver
    Case.step('uninstall DLB driver')
    acce.dlb_uninstall()


    

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
