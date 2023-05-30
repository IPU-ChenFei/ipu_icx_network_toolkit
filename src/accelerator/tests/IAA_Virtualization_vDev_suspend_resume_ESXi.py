import sys
import set_toolkit_src_root
from src.accelerator.lib.esxi import *
from src.accelerator.lib import *

CASE_DESC = [
    'Verify IAA device is available in guest VM after suspend and resume operation.'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    esxi = ESXi(sut)
    vm_name0 = 'centos_acce0'
    memsize = 4096
    # Prepare steps - Complete TC: https://hsdes.intel.com/appstore/article/#/15010838744  ESXi_IAX_Virtualization_SIOV_assign_vDev_Guest
    Case.prepare('Complete TC: https://hsdes.intel.com/appstore/article/#/15010838744  ESXi_IAX_Virtualization_SIOV_assign_vDev_Guest')
    acce.dsa_driver_install_esxi()
    my_os.warm_reset_cycle_step(sut)
    time.sleep(60)

    esxi.create_vm_from_template(vm_name0, f'{ESXI_CENTOS_TEMPLATE}', memsize)

    esxi.undefine_vm(vm_name0)

    esxi.attach_mdev_to_guest(vm_name0,'iaa')
    esxi.passthrough_memory_conf(memsize, vm_name0)

    esxi.define_vm(vm_name0)
    esxi.start_vm(vm_name0)
    #
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci | grep -i {acce.iax_id}')
    acce.check_keyword(['Intel Corporation Device'], out, f'device {acce.iax_id} not found')
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci -k | grep idxd')
    acce.check_keyword(['idxd'], out, 'idxd not found')

    Case.step('Configure WQ and run dmatest ')
    esxi.kernel_header_internal_devel(vm_name0)
    esxi.wq_configuration_dmatest(vm_name0, ip_name='iax') #iaa if fail

    #
    # step 1 - Login guest VM
    # step 2 - Verify iaa device available in guest VM
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci | grep -i {acce.iax_id}')
    acce.check_keyword(['Intel Corporation Device'], out, f'device {acce.iax_id} not found')
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci -k | grep idxd')
    acce.check_keyword(['idxd'], out, 'idxd not found')

    # step 3 - Suspend and Resume guest VM
    esxi.suspend_vm(vm_name0)
    esxi.resume_vm(vm_name0)
    #
    # step 4 - Login guest VM

    # step 5 - Verify iaa device available in guest VM
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci | grep -i {acce.iax_id}')
    acce.check_keyword(['Intel Corporation Device'], out, f'device {acce.iax_id} not found')
    _,out,_ = esxi.execute_vm_cmd(vm_name0, f'lspci -k | grep idxd')
    acce.check_keyword(['idxd'], out, 'idxd not found')

    # step 6 - Configure WQ and run dmatest
    esxi.wq_configuration_dmatest(vm_name0, ip_name='iax',config=False)
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
