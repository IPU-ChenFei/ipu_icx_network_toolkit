import sys
import set_toolkit_src_root
from src.accelerator.lib.esxi import *
from src.accelerator.lib import *

CASE_DESC = [
    'Pass vDev device to guest VM.Verify device is available in guest VM.'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    esxi = ESXi(sut)
    vm_name0 = 'centos_acce0'
    memsize = 8192
    # Prepare steps - Enable VT-d in BIOS and SRIOV
    Case.prepare('Enable VT-d and SRIOV in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    acce.dsa_driver_install_esxi()
    #

    # # # step 1 - Check iadx device in VMware OS
    Case.step('Check VM status and shutdown it.')
    esxi.create_vm_from_template(vm_name0, f'{ESXI_CENTOS_TEMPLATE}', memsize)
    vmlist = esxi.get_vm_list()
    if vm_name0 not in vmlist:
         sys.exit(1)
    esxi.undefine_vm(vm_name0)

    #step 2 - Configure device passthrough
    esxi.attach_mdev_to_guest(vm_name0, 'dsa', pci_num=0)
    esxi.passthrough_memory_conf(memsize, vm_name0)

    # step 3 - Re-register and Power-on guest VM
    esxi.define_vm(vm_name0)
    esxi.start_vm(vm_name0)

    # # step 4
    # # step 5 - Verify DSA device available in guest VM
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci | grep -i {acce.dsa_id}')
    acce.check_keyword(['Intel Corporation Device'], out, f'device {acce.dsa_id} not found')
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci -k | grep idxd')
    acce.check_keyword(['idxd'], out, 'idxd not found')

    # # step 6 - Configure WQ and run dmatest
    esxi.wq_configuration_dmatest(vm_name0, ip_name='dsa')
    esxi.undefine_vm(vm_name0)
    acce.uninstall_driver_esxi('iads')

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
