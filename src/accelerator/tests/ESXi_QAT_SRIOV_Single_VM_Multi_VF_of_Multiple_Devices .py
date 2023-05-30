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
    vm_name0 = 'centos_acce0'
    memsize = 4096
    # Prepare steps - Enable feature and install qat driver
    Case.prepare('Enable VT-d and SRIOV in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    sut.execute_shell_cmd(f'feature-state-util -e pciSriovPerDeviceMaxVfs')
    acce.qat_driver_install_esxi()
    #
    esxi.create_vm_from_template(vm_name0, f'{ESXI_CENTOS_TEMPLATE_PATH}centos_acce', memsize)
    # #
    # # #
    # step 1 - Create 2VFs per physical device. In a 2 socket system, there will be 8 QAT devices avaliable, so that by creating 2 VFs per device makes 16 VFs.
    Case.step('Create 2VFs per physical device. In a 2 socket system, there will be 8 QAT devices avaliable, so that by creating 2 VFs per device makes 16 VFs')
    vf_id_list_list = []
    for i in range(8):
        vf_id_list = esxi.create_vf('qat', i, 2)
        vf_id_list_list.append(vf_id_list)

    # step 2 - Enable VF passthrough function
    Case.step('Enable VF passthrough function')
    for vf_id_list in vf_id_list_list:
        for vf_id in vf_id_list:
            esxi.enable_vf_passthrough(vf_id)


    # step 3 - Make sure the VM is unregistered from ESXi while modifying the *.vmx file.
    Case.step('Make sure the VM is unregistered from ESXi while modifying the *.vmx file.')
    vmlist = esxi.get_vm_list()
    if vm_name0 not in vmlist:
         sys.exit(1)
    esxi.undefine_vm(vm_name0)

    # step 4 - Add VFs to Guest.
    # Configure device passthrough
    Case.step('Configure device passthrough')
    for vf_id_list in vf_id_list_list:
        esxi.attach_vf_list_to_guest(vm_name0,'qat', vf_id_list)
    esxi.passthrough_memory_conf(memsize, vm_name0)
    # #
    # step 5 - Re-register and Power-on guest VM
    Case.step('Re-register and Power-on guest VM')
    sut.execute_shell_cmd(f'vim-cmd solo/registervm {ESXI_CENTOS_TEMPLATE_PATH}{vm_name0}/{vm_name0}.vmx')
    esxi.start_vm(vm_name0)

    # step 6 - Install QAT driver and run the sample code
    Case.step('Install QAT driver and run the sample code')
    esxi.qat_dependency_install_vm(vm_name0)
    esxi.qat_install_vm(vm_name0, './configure --enable-icp-sriov=guest',False)

    # # step 7 - Then performance sample code can be executed.
    Case.step('Then performance sample code can be executed.')
    _,out,err = esxi.execute_vm_cmd(vm_name0, './cpa_sample_code',cwd=f"{QAT_DRIVER_PATH_L}/build",timeout=60*60)
    acce.check_keyword(['Sample code completed successfully'],out,'Sample code running fails')

    #
    esxi.undefine_vm(vm_name0)
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
