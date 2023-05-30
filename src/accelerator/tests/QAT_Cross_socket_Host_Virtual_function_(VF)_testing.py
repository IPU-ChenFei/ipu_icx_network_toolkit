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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011179814
    #TITLE: QAT_Cross_socket_Host_Virtual_function_(VF)_testing
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
        
        
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # Configuration:
        # https://hsdes.intel.com/appstore/article/#/15010469226
        # 1.Enable SRIOV and VT-D
        # EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) - Intel  VT For Directed I/O Enable
        # EDKII->Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support Enable
        ## Set BIOS knob: ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # CentOS_QAT_Dependency_need to install
        # :
        
        # dnf install -y  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel  yasm openssl-devel readline-devel  libgudev-devel.x86_64 gcc-c++
        # For yasm .rpm file download from below link:
        # https://centos.pkgs.org/7/epel-x86_64/yasm-1.2.0-4.el7.x86_64.rpm.html
        sutos.execute_cmd(sut, f'dnf install -y  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel  yasm openssl-devel readline-devel  libgudev-devel.x86_64 gcc-c++', timeout=10*60)
        # 2.
        # For qemu kvm steps Attachment is added.
        # Download QAT driver from BKC release , and sent it to /root/QAT.
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/QAT')
        sutos.execute_cmd(sut, f'\cp $SUT_TOOLS/qat20.l.0.9.0-00023_1.zip $Accelerator_REMOTE_TOOL_PATH/QAT')
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Make sure to set kernel command line parameter intel_iommu=on,sm_on"):
        # Make sure to set kernel command line parameter intel_iommu=on,sm_on
        #grubby --update-kernel=/boot/vmlinuz-'uname-r' --args="intel_iommu=on,sm_on"
        #reboot
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Generating grub configuration file ...")
        tcd.log("check args insert success after reboot.")
        tcd.log("# cat /proc/cmdline")
        tcd.log("BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.09_15_po.39.x86_64+server root=/dev/mapper/cl-r oot ro crashkernel=auto resume=/dev/mapper/cl-swap rd.lvm.lv=cl/root rd.lvm.lv=cl/swap rhgb quiet co nsole=ttyS0,115200 loglevel=7 console=tty0 intel_iommu=on,sm_on")
        ### Notes ###
        # Note : for RHEL OS
        # cd /etc/default/grub (intel_iommu=on,sm_off)
        # GRUB_TIMEOUT=5
        # GRUB_DISTRIBUTOR="$(sed 's, release .*$,,g' /etc/system-release)"
        # GRUB_DEFAULT=saved
        # GRUB_DISABLE_SUBMENU=true
        # GRUB_TERMINAL_OUTPUT="console"
        # GRUB_CMDLINE_LINUX="crashkernel=auto resume=/dev/mapper/cl00-swap rd.lvm.lv=cl00/root rd.lvm.lv=cl00/swap console=ttyS0,115200n8 console=tty0 intel_iommu=on,sm_on"
        # GRUB_DISABLE_RECOVERY="true"
        # GRUB_ENABLE_BLSCFG=true
        # Run the command : grub2-mkconfig -o /boot/efi/EFI/centos/grub.cfg
        # Reboot the system
        ##################
        
        
    ## 2
    if tcd.step("Install driver on host and enable SR-IOV"):
        # Install driver on host and enable SR-IOV
        # cd /root/QAT
        # ./configure --enable-icp-sriov=host
        # make install
        # make samples-install
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -i True', timeout=60*10)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'lsmod | grep qa\' -m "keyword" -l \'qat_4xxx\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Driver installation is successful. Once sample has been install, you can see the build folder")
        ##################
        
        
    ## 3
    if tcd.step("Modify device configuration files"):
        # Modify device configuration files
        # sed -i 's/ServicesEnabled.*/ServicesEnabled = asym/g' /etc/4xxxvf_dev*
        # python3 vf_conf_generator.py 0 asym off 4 16 2 56-111,168-223
        # (service, AT_Enable, AT_Mode='streaming', pf_number=0, vf_number=0, instance=0, cores=None)
        
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH/QAT && sed -i \'s/ServicesEnabled.*/ServicesEnabled = asym/g\' /etc/4xxxvf_dev*')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vf_conf_generator.py 0 asym off 4 16 2 56-111,168-223')
        ##################
        
        
    ## 4
    if tcd.step("(note: I just enable 4 PCMs on socket0 and each VF enable 2 asym instances, then set CoreAffinity for these 4*16*2 instances to cores of socket1 )"):
        # (note: I just enable 4 PCMs on socket0 and each VF enable 2 asym instances, then set CoreAffinity for these 4*16*2 instances to cores of socket1 )
        # (You can change the instance number for each VF and the core used, last 2 input of this script)
        # service qat_service stop
        # service qat_service start
        
        # Note: with our Beta RC, SVM is enabled by default with intel-next kernel if intel_iommu=on,sm_on
        # If you want to disable SVM, just add 'SVMEnabled =0' in the [GENERAL] section of VF configuration files
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_service_stop_start.py', timeout=10*60)
        ##################
        
        
    ## 5
    if tcd.step("Running test"):
        # Running test
        # ./build/cpa_sample_code runTests=30
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/run_qat_sample_code.py -q \'runTests=30\'', timeout=13*60*60)
        ##################
        
        
    ## 6
    if tcd.step("6"):
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_uninstall.py', timeout=10*60)
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
