import sys
import time

import set_toolkit_src_root
from src.accelerator.lib.esxi import *
from src.accelerator.lib import *

CASE_DESC = [
    'Verify DSA device is available in guest VM after suspend and resume operation. '
]



def test_steps(sut, my_os):
    acce = Accelerator(sut)
    esxi = ESXi(sut)
    esxi_rich = ESXi_Rich(sut)
    memsize = 4096

    #Prepare steps - call predefined steps
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

    # step 2 Enable SIOV
    esxi_rich.enable_siov_support()


    # step 3 - Install DLB driver on ESXI
    Case.step('Install DLB driver')
    acce.dlb_driver_install_esxi(True)
    acce.check_acce_device_esxi('dlb', cpu_num, True)

    # step 4 - Create VMs and attach dlb vf device
    cpu_num = esxi.get_cpu_num()
    device_num = acce.dlb_device_num
    dlb_device_num = cpu_num * device_num
    esxi_rich.clone_new_vm_rich(dlb_device_num)
    esxi_rich.attach_mdev_rich_vm('dlb', 1)
    esxi_rich.passthrough_memory_conf_rich_vm(memsize)
    esxi_rich.define_rich_vm()
    esxi_rich.start_rich_vm()

    # step 5 - install dlb driver and run ldb test
    esxi_rich.check_device_in_rich_vm(esxi, 'dlb', 1, True)
    esxi_rich.dlb_instll_rich_vm()
    dlb_tool_path = f'{DLB_DRIVER_PATH_L}dlb/libdlb'
    out_dict = esxi_rich.execute_rich_vm_cmd_parallel(f'LD_LIBRARY_PATH={dlb_tool_path} ./examples/ldb_traffic -n 1024',
                                                         cwd=dlb_tool_path, timeout=180)
    for vm_name in out_dict:
        _, out, _ = out_dict[vm_name]
        acce.check_keyword(['Received 1024 events'], out, 'Issue - Traffic move through the PF with some errors.')

    # #step 6 - undefine vm
    esxi_rich.undefine_rich_vm()
    acce.uninstall_driver_esxi('dlb')
    return 0
    #

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
