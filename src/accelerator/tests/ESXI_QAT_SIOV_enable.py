import sys
import set_toolkit_src_root
from src.accelerator.lib.esxi import *
from src.accelerator.lib import *

CASE_DESC = [
    'Verify DSA device is available in guest VM after suspend and resume operation. '
]



def test_steps(sut, my_os):
    acce = Accelerator(sut)
    esxi = ESXi(sut)
    # Prepare steps - Enable feature and install qat driver
    Case.prepare('Enable VT-d and SRIOV in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    acce.qat_driver_install_esxi()

    # #
    # # #
    # step 1 - Enable SIOV support
    Case.step('Enable SIOV support .')
    _,out,_ = sut.execute_shell_cmd(r"esxcli system settings kernel list | grep iovPasidMode | awk '{print $4}'", timeout=60)
    if 'TRUE' not in out:
        _, out, _ = sut.execute_shell_cmd(r"esxcli system settings kernel set --setting=iovPasidMode --value=TRUE",
                                          timeout=60)
    if 'TRUE' not in out:
        raise Exception('SIOV support is still not enabled')
    Case.step(' Reboot the system')
    my_os.warm_reset_cycle_step(sut)
    time.sleep(60)
    _,out,_ = sut.execute_shell_cmd(r"esxcli system settings kernel list | grep iovPasidMode | awk '{print $4}'", timeout=60)
    acce.check_keyword(['TRUE'], out, 'SIOV support is not enabled after rebooting')
    acce.uninstall_driver_esxi('qat')
    return

#
#
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
