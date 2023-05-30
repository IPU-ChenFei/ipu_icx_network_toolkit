# Tool Version [0.2.13]
CASE_DESC = [
    "it is a python script generated from validation language"
]

from dtaf_core.lib.tklib.basic.testcase import Result
from dtaf_core.lib.tklib.steps_lib.vl.vltcd import *
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell, BIOS_Menu
from dtaf_core.lib.tklib.steps_lib.os_scene import GenericOS
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from plat_feature_config import *


def test_steps(tcd):
    sut = tcd.sut
    sutos = tcd.sut.sutos
    assert (issubclass(sutos, GenericOS))
    hostos = tcd.hostos
    tools = get_tool(tcd.sut)
    bmc = get_bmc_info()


    # Tool Version [0.2.13]
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011179499
    #TITLE: QAT_Cross_socket_Physical_function_(PF)_testing
    #DOMAIN: accelerator
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Configuration:
        # https://hsdes.intel.com/appstore/article/#/15010469226
        ### Call TCDB accel.path_import Start
        sutos.execute_cmd(sut, f'rm -rf $HOME/.bashrc')
        sutos.execute_cmd(sut, f'cp /home/acce_tools/.bashrc $HOME/.bashrc')
        sutos.execute_cmd(sut, f'echo export API_SCRIPT={sutos.bkc_root_path}/accelerator_inband >> $HOME/.bashrc  #according to the handover instruction')
        sutos.execute_cmd(sut, f'python3 {sutos.bkc_root_path}/accelerator_inband/constant.py')
        sutos.execute_cmd(sut, f'source $HOME/.bashrc')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && find . -type f | xargs dos2unix;')
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH')
        ### Call TCDB accel.path_import End
        
        
        ## Boot to Linux
        boot_to(sut, sut.default_os)
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # 1.Disable VT-d  in BIOS
        # EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) - Intel  VT For Directed I/O
        # Disable
        ## Set BIOS knob: ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 2.check QAT device ,each socket have 4 devices
        #lspci |grep 4944
        # 6b:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # 70:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # 75:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # 7a:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # e8:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # ed:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # f2:00.0 Co-processor: Intel Corporation Device 4944 (rev 30)
        # f7:00.0 Co-processor: Intel Corporation Device 4944 (rev 30
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'lspci |grep -e 4944 -e 4940\' -m "keyword" -l \'Intel Corporation Device\'')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on\'')
        # 3. Check QAT drive,if there is no QAT Driver , please follow test 1509778665 to install QAT driver .
        # lsmod | grep qa
        # qat_4xxx               53248  0
        # intel_qat             356352  2 qat_4xxx,usdm_drv
        # uio                    20480  1 intel_qat
        # irqbypass              16384  4 intel_qat,idxd_mdev,vfio_pci,kvm
        sutos.execute_cmd(sut, f'dnf install -y  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel  yasm openssl-devel readline-devel  libgudev-devel.x86_64 gcc-c++', timeout=10*60)
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/QAT')
        sutos.execute_cmd(sut, f'\cp $QAT_DRIVER_NAME $Accelerator_REMOTE_TOOL_PATH/QAT')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -i False', timeout=10*60)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Modify device configuration files"):
        # Modify device configuration files
        # sed -i 's/ServicesEnabled.*/ServicesEnabled = asym/g' /etc/4xxx_dev*.conf
        
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH/QAT && sed -i \'s/ServicesEnabled.*/ServicesEnabled = asym/g\' /etc/4xxx_dev*.conf')
        ##################
        
        
    ## 2
    if tcd.step("Download the create_gen4_config.py utility."):
        # Download the create_gen4_config.py utility.
        
        # Check NUMA on SUT
        # lscpu
        
        # NUMA node0 CPU(s):   0-47,96-143
        # NUMA node1 CPU(s):   48-95,144-191
        
        
        # python3 create_gen4_config.py 0-1 28 48-95 0 0-0 asym 4xxx
        # python3 create_gen4_config.py 2-3 28 144-191 0 0-0 asym 4xxx
        # python3 create_gen4_config.py 4-5 28 0-47 0 0-0 asym 4xxx
        # python3 create_gen4_config.py 6-7 28 96-143 0 0-0 asym 4xxx
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_node_conf.py', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# lscpu")
        tcd.log("Architecture:        x86_64")
        tcd.log("CPU op-mode(s):      32-bit, 64-bit")
        tcd.log("Byte Order:          Little Endian")
        tcd.log("CPU(s):              192")
        tcd.log("On-line CPU(s) list: 0-191")
        tcd.log("Thread(s) per core:  2")
        tcd.log("Core(s) per socket:  48")
        tcd.log("Socket(s):           2")
        tcd.log("NUMA node(s):        2")
        tcd.log("...")
        tcd.log("...")
        tcd.log("NUMA node0 CPU(s):   0-47,96-143")
        tcd.log("NUMA node1 CPU(s):   48-95,144-191")
        ##################
        
        
    ## 3
    if tcd.step("service qat_service stop"):
        # service qat_service stop
        
        # service qat_service start
        
        # Note: with our Beta RC, SVM is enabled by default with intel-next kernel if intel_iommu=on,sm_on
        # If you want to disable SVM, just add 'SVMEnabled =0' in the [GENERAL] section of VF configuration files
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_service_stop_start.py', timeout=10*60)
        ##################
        
        
    ## 4
    if tcd.step("Running test"):
        # Running test
        # cd /root/QAT
        # ./build/cpa_sample_code  runTests=30
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/run_qat_sample_code.py -q \'runTests=30\'', timeout=13*60*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("The sample code is run completed")
        tcd.log("with no error. the last line is \"Sample code completed successfully\"")
        tcd.log("qaeMemInit started")
        tcd.log("icp_sal_userStartMultiProcess(\"SSL\") started")
        tcd.log("*** QA version information ***")
        tcd.log("device ID= 0")
        tcd.log("software = 1.1.0")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Sample code completed successfully.")
        ##################
        
        
    ## 5
    if tcd.step("5"):
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_uninstall.py', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("uninstall qat driver")
        ##################
        
        


def clean_up(sut):
    pass


def test_main():
    tcd = TestCase(globals(), locals())
    try:
        tcd.start(CASE_DESC)
        test_steps(tcd)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        tcd.end()
        clean_up(tcd)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
