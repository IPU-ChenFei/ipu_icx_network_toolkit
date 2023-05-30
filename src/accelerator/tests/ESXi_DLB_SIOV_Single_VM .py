import sys
import time

import set_toolkit_src_root
from src.accelerator.lib.esxi import *
from src.accelerator.lib import *

CASE_DESC = [
    ''
]

def test_steps(sut, my_os):
    acce = Accelerator(sut)
    esxi = ESXi(sut)
    vm_name0 = 'centos_acce0'
    memsize = 8192
    template = f'{ESXI_RHEL_TEMPLATE}'

# #Prepare steps - call predefined steps
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

    # step 2 Enable pciSriovPerDeviceMaxVfs
    sut.execute_shell_cmd(f'feature-state-util -e pciSriovPerDeviceMaxVfs')

    # step 3 - Install DLB driver on ESXI
    Case.step('Install DLB driver')
    acce.dlb_driver_install_esxi(True)
    acce.check_acce_device_esxi('dlb', cpu_num, True)

    # step 4 create VM and attach DLB SRIOV device to guest vm
    esxi.clone_new_vm(vm_name0, template)
    esxi.undefine_vm(vm_name0)
    esxi.config_dlb_vdev(1)
    esxi.attach_mdev_to_guest(vm_name0, 'dlb')
    esxi.passthrough_memory_conf(memsize, vm_name0)

    # step 5 start VM and install dlb driver
    esxi.define_vm(vm_name0)
    esxi.start_vm(vm_name0)
    acce.check_device_in_vm(esxi, vm_name0, 'dlb', 1)
    esxi.kernel_header_devel_vm(vm_name0)
    esxi.dlb_install_vm(vm_name0)

    # Step 6 - Run ldb_traffic example on the Guest VM
    Case.prepare('Ruun ldb_traffic example on the Guest VM')
    dlb_tool_path = f'{DLB_DRIVER_PATH_L}dlb/libdlb'
    ret, out, _ = esxi.execute_vm_cmd(vm_name0, f'LD_LIBRARY_PATH={dlb_tool_path} ./examples/ldb_traffic -n 1024', timeout=180,
                                      cwd=dlb_tool_path
                                      )
    Case.expect('Run ldb_traffic successfully', ret == 0)
    acce.check_keyword(['Received 1024 events'], out, 'Issue - Traffic move through the PF with some errors.')

    #step 6 shutdown vm and uninstall dlb driver
    esxi.shutdown_vm(vm_name0)
    esxi.undefine_vm(vm_name0)
    esxi.remove_vm_files(vm_name0)






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
