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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010635661
    #TITLE: IAX_SIOV_mdev_user_test_multi_VM_L
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
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && find . -type f | xargs dos2unix;')
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH')
        ### Call TCDB accel.path_import End
        
        
        ## Boot to Linux
        boot_to(sut, sut.default_os)
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        sutos.execute_cmd(sut, f'dmesg -C')
        # 1.BIOS Configuration
        # Verify the following BIOS settings.
        # EDKII Menu > Socket Configuration > IIO configuration > PCIe ENQCMD > ENQCMDS = enabled
        # EDKII Menu > Socket Configuraiton > IIO Configuration >IOAT configuration >socket <n> IOAT configure > DSA = enabled
        # Notes: This is only support on SPR, not support GNR
        # EDKII Menu > Socket Configuraiton > IIO Configuration > VT-d = enabled
        # EDKII Menu > Socket Configuration > Processor Configuration > VMX = enabled
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 2.Download img file from link which is release by BKC.
        #cd /home
        #wget https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202111012334/images/centos-8.4.2105-embargo-coreserver-202111012334.img.xz
        #unxz  centos-8.4.2105-embargo-coreserver-202111012334.img.xz
        #
        # 3.Kernel parameters in host:
        # grubby --args="
        # intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update
        # -kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        # Note: For intel next kernel 5.15 or newer , '
        # idxd.legacy_cdev_load=1
        
        # modprobe.blacklist=idxd_uacce
        # '
        # is no longer needed
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # 4.
        # cp or git clone accel-random-config-and-test to /root/DSA
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        # 5.Install kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
        # rpm -ivhf kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS &&  rpm -ivhf $INTERNAL_MODULE_NAME', no_check=True)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Linux Kernel parameters"):
        # Linux Kernel parameters
        # Check Linux command line.
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Kernel parameters in host:")
        tcd.log("intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce")
        ### Notes ###
        # For intel next kernel 5.15 or newer , 'idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce'  is no longer needed
        ##################
        
        
    ## 2
    if tcd.step("Configure mdev work-queues"):
        # Configure mdev work-queues
        # 1. Change to PV DSA IAX Test Directory.
        # cd /root/DSA/accel-random-config-and-test
        
        # 2. Configure work-queues.
        # ./Setup_Randomize_IAX_Conf.sh -ma
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c \'Setup_Randomize_IAX_Conf.sh -ma\'', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Work-queues are configured successfully.")
        tcd.log("# ./Setup_Randomize_IAX_Conf.sh -ma")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("iax3 iax1 iax7 iax9 iax13 iax5 iax15 iax11")
        tcd.log("enabled 8 device(s) out of 8")
        tcd.log("Enabling work-queues:")
        tcd.log("iax3/wq3.6 iax3/wq3.7 iax3/wq3.2 iax3/wq3.3 iax3/wq3.0 iax3/wq3.1 iax3/wq3.5 iax3/wq3.4 iax1/wq1.4 iax1/wq1.5 iax1/wq1.7 iax1/wq1.0 iax1/wq1.2 iax1/wq1             .6 iax1/wq1.3 iax1/wq1.1 iax7/wq7.6 iax7/wq7.7 iax7/wq7.5 iax7/wq7.4 iax7/wq7.1 iax7/wq7.0 iax7/wq7.3 iax7/wq7.2 iax9/wq9.0 iax9/wq9.3 iax9/wq9.1 iax9/             wq9.4 iax9/wq9.5 iax9/wq9.6 iax9/wq9.2 iax9/wq9.7 iax13/wq13.1 iax13/wq13.2 iax13/wq13.3 iax13/wq13.0 iax13/wq13.7 iax13/wq13.5 iax13/wq13.4 iax13/wq13             .6 iax5/wq5.2 iax5/wq5.7 iax5/wq5.3 iax5/wq5.0 iax5/wq5.6 iax5/wq5.1 iax5/wq5.4 iax5/wq5.5 iax15/wq15.1 iax15/wq15.7 iax15/wq15.5 iax15/wq15.2 iax15/wq             15.3 iax15/wq15.6 iax15/wq15.4 iax15/wq15.0 iax11/wq11.5 iax11/wq11.6 iax11/wq11.7 iax11/wq11.4 iax11/wq11.0 iax11/wq11.2 iax11/wq11.1 iax11/wq11.3")
        tcd.log("enabled 64 wq(s) out of 64")
        ##################
        
        
    ## 3
    if tcd.step("Modify \"VM_IMAGE=\" and \"VM_BIOS =\"variable in \"config.sh\""):
        # Modify "VM_IMAGE=" and "VM_BIOS ="variable in "config.sh"
        # cd /root/DSA/accel-random-config-and-test
        #sed -i 's/VM_IMAGE=.*/VM_IMAGE=<image_path>/g' config.sh
        #sed -i 's/VM_BIOS=.*/VM_BIOS=<bios_path>/g' config.sh
        
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && sed -i \'s/VM_IMAGE=.*/VM_IMAGE=$CENTOS_IMG_NAME/g\' config.sh')
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && sed -i \'s/VM_BIOS=.*/VM_BIOS=$OVMF_NAME/g\' config.sh')
        ##################
        
        
    ## 4
    if tcd.step("Launch multiple virtual machines."):
        
        # Launch multiple virtual machines.
        # Copy Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh to /root/DSA/accel-random-config-and-test
        # ./Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh -i -n10 -c1 -m1
        
        sutos.execute_cmd(sut, f'chmod 777 $API_SCRIPT/Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh $ACCE_RANDOM_CONFIG_TEST_PATH_L')
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && ./Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh -i -n10 -c1 -m1', timeout=10*60)
        tcd.sleep(30)
        ##################
        
        
    ## 5
    if tcd.step("Login VMs and prepare test env."):
        # Login VMs and prepare test env.
        # 1.Copy random tools to guests
        #sftp hostip
        # >get -r /root/DSA/accel-random-config-and-test /root
        # >bye
        # 2.Change cmdline to "intel_iommu=on,sm_on no5lvl"
        #grubby --update-kernel=/boot/vmlinuz-'uname-r' --args="intel_iommu=on,sm_on no5lvl"
        #reboot
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py -n 10', timeout=30*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $ACCE_RANDOM_CONFIG_TEST_PATH_L" -n 10', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$ACCE_RANDOM_CONFIG_TEST_PATH_L" -d "$ACCE_RANDOM_CONFIG_PATH_L" -n 10', timeout=10*60)
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on no5lvl\'" -n 10')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "reboot" -n 10')
        tcd.sleep(120)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on no5lvl\'" -n 10')
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DSA_NAME" -d "$SUT_TOOLS" -n 10', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools" -n 10', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum groupinstall -y \'Development Tools\'" -n 10', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y asciidoc xmlto libuuid-devel json-c-devel" -n 10', no_check=True, timeout=20*60)
        ##################
        
        
    ## 6
    if tcd.step("Check IAX device in guests"):
        # Check IAX device in guests
        #lspci | egrep '0b25|0cfe'
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c \'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "lspci |grep -e 0b25 -e 0cfe" -m "keyword" -l "Intel Corporation Device"\' -n 10', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("IAX device show in guests")
        tcd.log("# lspci | egrep \'0b25|0cfe\'")
        tcd.log("00:03.0 System peripheral: Intel Corporation Device 0cfe")
        ##################
        
        
    ## 7
    if tcd.step("Run dmatest on VMs ."):
        # Run dmatest on VMs .
        # cd /root/accel-random-config-and-test/
        #modprobe idxd_ktest   ## Only for intel next kernel 5.12 .
        # ./Guest_Mdev_Randomize_IAX_Conf.sh -u
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/accel_config_install.py" -n 10', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/lnx_exec_with_check.py -c \'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && ./Guest_Mdev_Randomize_IAX_Conf.sh -u\' -m \'keyword\' -l \'enabled 1 wq(s) out of 1\'" -n 10', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Kernel type work-queues configured in virtual machines.")
        tcd.log("# ./Guest_Mdev_Randomize_IAX_Conf.sh -u")
        tcd.log("Configuring 1 IAX Devices")
        tcd.log("iax0; numa_node: -1; max_wq_size: 9; op_cap: 0xd 0x7f331c 0x0 0x0; gen_cap: 0x71f10001f0115; token_limit: 0; max_tokens: 0; max_batch: 1; max_transfer_size: 2147483648; ims_size: 0; cdev_major: 237; iax_clients: 0;")
        tcd.log("wq: wq0.0; Group: 0; Size: 9; Threshold: 0; Priority: 7; Type: user; Mode: dedicated; Block On Fault: 0; Name: wq0.0")
        tcd.log("Enabling work-queues:")
        tcd.log("iax0/wq0.0")
        tcd.log("[   43.750681] user wq0.0: wq wq0.0 enabled")
        tcd.log("enabled 1 wq(s) out of 1")
        ##################
        
        
    ## 8
    if tcd.step("./Guest_Mdev_Randomize_IAX_Conf.sh -r"):
        #./Guest_Mdev_Randomize_IAX_Conf.sh -r
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/lnx_exec_with_check.py -c \'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && ./Guest_Mdev_Randomize_IAX_Conf.sh -r\' -m \'keyword\' -l \'24 of 24 tests passed\'" -n 10', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("dmatest runs on each virtual machine without errors.")
        tcd.log("Logs show dmatest completed successfully on each thread.")
        tcd.log("#./Guest_Mdev_Randomize_IAX_Conf.sh -r")
        tcd.log("Running iax_test with # of WQs: 1")
        tcd.log("Using tests:    ./iaxbin/crc64 ./iaxbin/crc64_noInvert ./iaxbin/post_compress ./iaxbin/post_decompress ./iaxbin/post_de_scan ./iaxbin/post_expand ./iaxbin/post_expand1 ./iaxbin/post_extract ./iaxbin/post_extract1 ./iaxbin/post_find ./iaxbin/post_find1 ./iaxbin/post_rle ./iaxbin/post_rle1 ./iaxbin/post_scan ./iaxbin/post_select ./iaxbin/post_select1 ./iaxbin/post_set ./iaxbin/post_set1 ./iaxbin/test_compress ./iaxbin/test_decompress ./iaxbin/zcompress16 ./iaxbin/zcompress32 ./iaxbin/zdecompress16 ./iaxbin/zdecompress32")
        tcd.log("24 of 24 tests passed")
        ##################
        
        
    ## 9
    if tcd.step("Verify no errors in host dmesg"):
        
        # Verify no errors in host dmesg
        # dmesg
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py -i \'QAT: Failed to enable AER, error code -5,Record Serialization Table (ERST) support is initialized\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No errors reported")
        ##################
        
        
    ## 10
    if tcd.step("Shutdown virtual machines on Host"):
        # Shutdown virtual machines on Host
        # ./Setup_Mdev_Multi_VM_DSA_IAX.sh -s
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "shutdown now" -n 10', no_check=True, timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Virtual machines shutdown")
        ##################
        
        
    ## 11
    if tcd.step("Repeat steps 5-8 10 times .Please use different TCP port , mdev for VMs"):
        # Repeat steps 5-8 10 times .Please use different TCP port , mdev for VMs
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("test successfully")
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
