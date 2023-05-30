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
    # Prepare steps - Enable feature and install qat driver
    Case.prepare('Enable VT-d and SRIOV in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    sut.execute_shell_cmd(f'feature-state-util -e pciSriovPerDeviceMaxVfs')
    acce.qat_driver_install_esxi()

    vm_list = esxi_rich.clone_new_vm_rich(4, template=f'{ESXI_CENTOS_TEMPLATE}')
    logger.info(f'vms {vm_list} created')
    # step 1 - Create six VF .
    Case.step('Create six VF.')
    # step 2 - Enable VF passthrough function
    Case.step('Enable VF passthrough function')
    vf_id_list1 = esxi.create_vf('qat', 0, 6)
    vf_id_list2 = esxi.create_vf('qat', 1, 6)
    vf_id_list3 = esxi.create_vf('qat', 4, 6)
    vf_id_list4 = esxi.create_vf('qat', 5, 6)

    vf_id_list_list = [vf_id_list1,vf_id_list2,vf_id_list3,vf_id_list4]

    # step 3 - Make sure the VM is unregistered from ESXi while modifying the *.vmx file.
    Case.step('Make sure the VM is unregistered from ESXi while modifying the *.vmx file.')
    esxi_rich.undefine_rich_vm(vm_list)

    # step 4 - Add VFs to Guest.
    # Configure device passthrough
    Case.step('Configure device passthrough')
    for i,vm_name in enumerate(vm_list):
        esxi.attach_vf_list_to_guest(vm_name,'qat', vf_id_list_list[i])
        esxi.passthrough_memory_conf(memsize, vm_name)

    # step 5 - Re-register and Power-on guest VM
    Case.step('Re-register and Power-on guest VM')
    esxi_rich.define_rich_vm(vm_list)
    esxi_rich.start_rich_vm(vm_list)


    # step 6 - Install QAT driver and run the sample code
    Case.step('Install QAT driver and run the sample code')
    esxi_rich.qat_dependency_install_rich_vm(vm_list)
    esxi_rich.qat_install_rich_vm('./configure --enable-icp-sriov=guest',False,vm_list)

    # # step 7 - Then performance sample code can be executed.
    Case.step('Then performance sample code can be executed.')
    out_dict = esxi_rich.execute_rich_vm_cmd_parallel('./cpa_sample_code',vm_list,cwd=f"{QAT_DRIVER_PATH_L}/build",timeout=60*60)
    for vm_name in out_dict:
        _,out,_ = out_dict[vm_name]
        acce.check_keyword(['Sample code completed successfully'],out,'Sample code running fails')

    esxi_rich.undefine_rich_vm(vm_list)
    acce.uninstall_driver_esxi('qat')
    return 0

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
