# Tool Version [0.2.11]
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

    if tcd.prepare("boot to OS"):
        boot_to(sut, sut.default_os)


    # Tool Version [0.2.11]
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011083218
    #TITLE: QAT PFLR - Functional level reset of physical devices
    #DOMAIN: accelerator
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        
        ### Call TCDB accel.path_import Start
        sutos.execute_cmd(sut, f'rm -rf $HOME/.bashrc')
        sutos.execute_cmd(sut, f'cp /home/acce_tools/.bashrc $HOME/.bashrc')
        sutos.execute_cmd(sut, f'echo export API_SCRIPT={sutos.bkc_root_path}/accelerator_inband >> $HOME/.bashrc  #according to the handover instruction')
        sutos.execute_cmd(sut, f'python3 {sutos.bkc_root_path}/accelerator_inband/constant.py')
        sutos.execute_cmd(sut, f'source $HOME/.bashrc')
        
        #Execute Command: echo export ACCEL_CONFIG_PKG={sutos.bkc_root_path}/domains/acce_tools >> $HOME/.bashrc
        #Execute Command: echo export SUT_TOOLS=/home/acce_tools >> $HOME/.bashrc
        #Execute Command: echo export Accelerator_REMOTE_TOOL_PATH={sutos.bkc_root_path}/domains/acce_tools >> $HOME/.bashrc
        #Execute Command: echo export ACCE_RANDOM_CONFIG_NAME=$SUT_TOOLS/accel-random-config-and-test-main.zip >> $HOME/.bashrc
        #Execute Command: echo export ACCE_RANDOM_CONFIG_PATH_L=$Accelerator_REMOTE_TOOL_PATH/acce_random_config >> $HOME/.bashrc
        #Execute Command: echo export DSA_NAME=$SUT_TOOLS/idxd-config-accel-config*.zip >> $HOME/.bashrc
        #Execute Command: echo export DSA_PATH_L=$Accelerator_REMOTE_TOOL_PATH/DSA >> $HOME/.bashrc
        ### Call TCDB accel.path_import End
        
        
        # Configuration:
        # https://hsdes.intel.com/appstore/article/#/15010469226
        # Disable VT-d  in BIOS
        # EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) - Intel  VT For Directed I/O Disable
        # CentOS_QAT_Dependency_need to install
        # :
        
        # dnf install -y  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel  yasm openssl-devel readline-devel  libgudev-devel.x86_64
        # gcc-c++
        # Install Kernel Devel  rpm files.
        #rpm -ivh <kernel-devel-flie>
        # For qemu kvm steps Attachment is added.
        # Download QAT driver from BKC release , and sent it to /root/QAT.
        ## Set BIOS knob: ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x0, VTdSupport=0x0, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        sutos.execute_cmd(sut, f'dnf install -y  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel  yasm openssl-devel readline-devel  libgudev-devel.x86_64 gcc-c++', timeout=10*60)
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/QAT')
        sutos.execute_cmd(sut, f'\cp $QAT_DRIVER_NAME $Accelerator_REMOTE_TOOL_PATH/QAT')
        # QAT Sample code parameters
        # For RSA/DSA/ECDA/DH you need to have device configured with asymmetric service.
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Extract QAT package and build driver:"):
        # Extract QAT package and build driver:
        
        # cd /root/QAT
        # unzip qat20.l.0.5.6-00008.zip
        # tar -zxvf QAT20.L.0.5.6-00008.tar.gz
        # ./configure
        # make all
        # make install
        # make samples-install
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -i False', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("the CLI exec successfully and returns a zero return code.")
        ##################
        
        
    ## 2
    if tcd.step("Run cpa_sample_code."):
        # Run cpa_sample_code.
        # cd build
        #./cpa_sample_code
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/run_qat_sample_code.py -q \'\'', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("The sample code is run completed")
        tcd.log("with no error. the last line is \"Sample code completed successfully\"")
        tcd.log("#./cpa_sample_code")
        tcd.log("....")
        tcd.log("....")
        tcd.log("Clock Cycles Start     4000341580185")
        tcd.log("Clock Cycles End       4000428212699")
        tcd.log("---------------------------------------")
        tcd.log("Sample code completed successfully.")
        ### Notes ###
        # New
        ##################
        
        
    ## 3
    if tcd.step("Perform Function level reset on QAT virtual function and rerun the cpa_sample_code again"):
        # Perform Function level reset on QAT virtual function and rerun the cpa_sample_code again
        
        # adf_ctl restart
        
        #./cpa_sample_code
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_reset_12h.py -m \'physical\'', timeout=13*60*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# adf_ctl restart")
        tcd.log("#./cpa_sample_code")
        tcd.log("....")
        tcd.log("....")
        tcd.log("Clock Cycles Start 4000341580185")
        tcd.log("Clock Cycles End 4000428212699")
        tcd.log("---------------------------------------")
        tcd.log("Sample code completed successfully.")
        ##################
        
        
    ## 4
    if tcd.step("Repeat the Step-3 for 12 hours"):
        # Repeat the Step-3 for 12 hours
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Sample code completed successfully")
        ##################
        
        
    ## 5
    if tcd.step("5"):
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_uninstall.py', timeout=10*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
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
