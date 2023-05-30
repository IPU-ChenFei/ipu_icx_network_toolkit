import sys
import time

import set_toolkit_src_root
from src.accelerator.lib.esxi import *
from src.accelerator.lib import *

CASE_DESC = [
    'Check QAT device',
    'QAT driver install',
    'check cpa_sample_code file generate'
]

def up_all_qat_device_vm(esxi,vm_name):
    _,out,err = esxi.execute_vm_cmd(vm_name, f"adf_ctl status",timeout=60*60)
    line_list = out.strip().split('\n')
    for line in line_list:
        qat_dev = line.split('-')[0].strip(' ')
        if 'state: down' in line:
            _, out, err = esxi.execute_vm_cmd(vm_name, f"./build/adf_ctl {qat_dev} up", timeout=60 * 60)
    return 0


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    esxi = ESXi(sut)
    vm_name0 = 'centos_acce0'
    memsize = 4096
    # Prepare steps - install the driver
    Case.step('Install QAT driver')
    # cpu_num = acce.get_cpu_num_esxi()
    cpu_num = int(esxi.get_cpu_num())
    acce.qat_driver_install_esxi()
    acce.check_acce_device_esxi('qat', cpu_num, True)

    esxi.create_vm_from_template(vm_name0, f'{ESXI_CENTOS_TEMPLATE}', memsize)

    # Step 1 - Make sure the VM is unregistered from ESXi while modifying the *.vmx file
    Case.step('Make sure the VM is unregistered from ESXi while modifying the *.vmx file')
    esxi.undefine_vm(vm_name0)

    # Step 2 - Configure device passthrough
    Case.step('Configure device passthrough ')
    esxi.attach_vqat_to_guest(vm_name0, 'vqat_sym', pci_num=0)
    esxi.passthrough_memory_conf(memsize, vm_name0)

    # step 3 - Re-register and Power-on guest VM
    Case.step('Re-register and Power-on guest VM')
    esxi.define_vm(vm_name0)
    esxi.start_vm(vm_name0)
    #
    # step 4 - Login guest VM
    # step 5 - Check devices assigned
    Case.step('Check devices assigned')
    _,out,err = esxi.execute_vm_cmd(vm_name0, f"lspci -v -d 8086:{acce.qat_mdev_id} -vmm | grep -E 'SDevice | 0000'",timeout=60*60)
    acce.check_keyword(['SDevice'],out,'Device not exists')

    # step 6 - Upload QAT drive to guest and install QAT Driver and Run basic
    Case.step('Upload QAT drive to guest and install QAT Driver and Run basic')
    esxi.qat_dependency_install_vm(vm_name0)
    esxi.qat_install_vm(vm_name0, './configure --enable-icp-sriov=guest',False)

    # step 7 - Check vqat device status , if device is down , please enable it.
    Case.step('Check vqat device status , if device is down , please enable it.')
    _,out,err = esxi.execute_vm_cmd(vm_name0, f"lspci -vd :{acce.qat_mdev_id}",timeout=60*60)
    acce.check_keyword(['Intel Corporation Device'], out, 'vqat device not exists')
    up_all_qat_device_vm(esxi,vm_name0)

    # step 8 - Run QAT workload which uses SIOV Virtual device interface
    Case.step('Run QAT workload which uses SIOV Virtual device interface')
    _,out,_ = esxi.execute_vm_cmd(vm_name0, './cpa_sample_code signOfLife=1',cwd=f"{QAT_DRIVER_PATH_L}/build",timeout=60*60)
    acce.check_keyword(['Sample code completed successfully.'],out,'qat is down after running the sample code')
    _,out,_ = esxi.execute_vm_cmd(vm_name0, ' ./cpa_sample_code runTests=63',cwd=f"{QAT_DRIVER_PATH_L}/build",timeout=60*60)
    acce.check_keyword(['Sample code completed successfully.'],out,'qat is down after running the sample code')


    esxi.undefine_vm(vm_name0)
    acce.uninstall_driver_esxi('qat')

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
