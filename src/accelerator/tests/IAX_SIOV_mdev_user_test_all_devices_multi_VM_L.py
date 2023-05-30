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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011075288
    #TITLE: IAX_SIOV_mdev_user_test_all_devices_multi_VM_L
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
        
        sutos.execute_cmd(sut, f'dmesg -C')
        # Note: SUT need enough memory to launch each VM. Verify available memory and VM settings.
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
        # For intel next kernel 5.15 or newer ,
        # '
        # idxd.legacy_cdev_load=1
        # modprobe.blacklist=idxd_uacce
        # '
        # is no longer needed
        # grubby --args="intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # Kernel 5.15+:
        # intel_iommu=on,sm_on,iova_sl
        # 5.Kernel parameters in guest:
        # grubby --args="
        # intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update
        # -kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        # Kernel 5.15+:
        # intel_iommu=on,sm_on no5lvl
        # 4.
        # cp or git clone accel-random-config-and-test to /root/DSA
        
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        sutos.execute_cmd(sut, f'rm -rf $ACCE_RANDOM_CONFIG_PATH_L')
        sutos.execute_cmd(sut, f'mkdir -p $ACCE_RANDOM_CONFIG_PATH_L')
        sutos.execute_cmd(sut, f'\cp $ACCE_RANDOM_CONFIG_NAME $ACCE_RANDOM_CONFIG_PATH_L', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_PATH_L && unzip -o accel-random-*')
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
        # Kernel 5.15+:
        # intel_iommu=on,sm_on,iova_sl
        ##################
        
        
    ## 2
    if tcd.step("Launch virtual machine image:"):
        # Launch virtual machine image:
        
        
        # qemu-system-x86_64 \
        # -name test \
        # -machine q35 \
        # -enable-kvm \
        # -global kvm-apic.vapic=false \
        # -m 10240 \
        # -cpu host \
        # -drive format=raw,file=/home/centos-8.4.2105-embargo-coreserver-<current version>.img \
        # -bios /home/OVMF.fd \
        # -smp 16 \
        # -serial mon:stdio \
        # -nic user,hostfwd=tcp::2222-:22 \
        # -nographic
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -n \'1\' -f $CENTOS_IMG_NAME', timeout=10*60)
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_startvm.py -c "/usr/libexec/qemu-kvm -name guestVM0 -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 8192 -cpu host -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -drive format=raw,file=/home/vm0.img -bios /home/OVMF.fd -smp 4 -serial mon:stdio -nographic"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py -p 2222', timeout=30*60)
        
        ##################
        
        
    ## 3
    if tcd.step("Config the kernel cmdline in gust vm and cp file to vm."):
        # Config the kernel cmdline in gust vm and cp file to vm.
        #grubby --args="intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"  --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        #sftp hostip
        # >get -r /root/DSA/accel-random-config-and-test /root
        # >bye
        #reboot
        # Wait os reboot done then shutdown vm
        #shutdown now
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on no5lvl\'"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "reboot"', timeout=10*60)
        tcd.sleep(120)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $ACCE_RANDOM_CONFIG_TEST_PATH_L" -p 2222', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$ACCE_RANDOM_CONFIG_TEST_PATH_L" -d "$ACCE_RANDOM_CONFIG_PATH_L" -p 2222', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DSA_NAME" -d "$SUT_TOOLS" -p 2222', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools" -p 2222', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c \'yum groupinstall -y "Development Tools"\' -p 2222', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y asciidoc xmlto libuuid-devel json-c-devel" -p 2222', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/accel_config_install.py" -p 2222', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "shutdown now"', no_check=True, timeout=10*60)
        ##################
        
        
    ## 4
    if tcd.step("Config VM_IMAGE and VM_BIOS path in config.sh"):
        # Config VM_IMAGE and VM_BIOS path in config.sh
        # cd /root/DSA/accel-random-config-and-test
        #vi config.sh
        # VM_IMAGE="/home/centos-8.4.2105-embargo-coreserver-202111012334.img" # location of VM guest image
        # VM_BIOS="/home/OVMF.fd" # location of VM guest BIOS
        
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && sed -i \'s#VM_IMAGE=.*#VM_IMAGE=/home/vm0.img#g\' config.sh')
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && sed -i \'s#VM_BIOS=.*#VM_BIOS=/home/OVMF.fd#g\' config.sh')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# cat config.sh")
        tcd.log("# configurables. Modify this file for your specific configuration")
        tcd.log("DSA_TEST=${DIR}/dsa_test/dsa_test # location of \"dsa_test\" executable")
        tcd.log("IAX_TEST=${DIR}/iax_test/iax_test # location of \"iax_test\" executable")
        tcd.log("VM_IMAGE=\"/home/centos-8.4.2105-embargo-coreserver-202111012334.img\" # location of VM guest image")
        tcd.log("VM_BIOS=\"/home/OVMF.fd\" # location of VM guest BIOS")
        tcd.log("VM_NETWORK=\"-nic user,hostfwd=tcp::2222-:22\" # VM guest network device")
        tcd.log("VM_MEMORY=4096 # Memory allocation for VM (MiB)")
        tcd.log("# default QEMU iommu device")
        tcd.log("qemu_iommu_device=\"-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=\"modern\",device-iotlb=on,aw-bits=48\"")
        ##################
        
        
    ## 5
    if tcd.step("Configure mdev work-queues and start virtual machine"):
        # Configure mdev work-queues and start virtual machine
        # 1. Configure work-queues.
        # ./Setup_Randomize_IAX_Conf.sh -maD
        
        # 2. Start VM using launch script
        # ./Setup_Mdev_Multi_VM_DSA_IAX.sh -i -c1 -m1 -n<#of MDEVS>
        
        # Note: replace  " <# of MDEVS> " with the total number of WQs/MDEVs configured previous step . This will launch the provided number of VMs with one MDEV per VM.
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c \'Setup_Randomize_IAX_Conf.sh -maD\' -u "False"', timeout=20*60)
        sutos.execute_cmd(sut, f'chmod 777 $API_SCRIPT/Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/Setup_Mdev_Multi_VM_DSA_IAX_modify_for_auto.sh $ACCE_RANDOM_CONFIG_TEST_PATH_L')
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && ./Setup_Mdev_Multi_VM_DSA_IAX.sh -i -c1 -m1 -n64', timeout=20*60)
        tcd.sleep(30)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Work-queues are configured successfully.")
        tcd.log("# ./Setup_Randomize_IAX_Conf.sh -maD")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("iax7 iax3 iax5 iax1")
        tcd.log("enabled 4 device(s) out of 4")
        tcd.log("Enabling work-queues:")
        tcd.log("iax7/wq7.5 iax7/wq7.6 iax7/wq7.7 iax7/wq7.3 iax7/wq7.1 iax7/wq7.4 iax7/wq7.2 iax7/wq7.0 iax3/wq3.6 iax3/wq3.3 iax3/wq3.0 iax3/wq3.2 iax3/wq3.1 iax3/wq3.4 iax3/wq3.7 iax3/wq3.5 iax5/wq5.3 iax5/wq5.2 iax5/wq5.4 iax5/wq5.1 iax5/wq5.7 iax5/wq5.0 iax5/wq5.6 iax5/wq5.5 iax1/wq1.6 iax1/wq1.5 iax1/wq1.2 iax1/wq1.7 iax1/wq1.1 iax1/wq1.4 iax1/wq1.3 iax1/wq1.0")
        tcd.log("enabled 32 wq(s) out of 32")
        tcd.log("...")
        tcd.log("...")
        tcd.log("# ./Setup_Mdev_Multi_VM_DSA_IAX.sh -i -c1 -m1 -n2")
        tcd.log("Shutting down VMs...")
        tcd.log("Generating QCOW images using /home/centos-8.4.2105-embargo-coreserver-202111012334.img as the original drive image.")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Checking for iax devices.")
        tcd.log("Executing lspci | egrep \'0b25|0cfe\' on VM using port 2201...")
        tcd.log("root@localhost\'s password:")
        tcd.log("00:03.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("...")
        tcd.log("...")
        tcd.log("### VM SSH Connection Info ###")
        tcd.log("VM running on port 2201...")
        tcd.log("to connect to VM: ssh -p 2201 localhost")
        tcd.log("VM running on port 2202...")
        tcd.log("to connect to VM: ssh -p 2202 localhost")
        tcd.log("...")
        tcd.log("...")
        ##################
        
        
    ## 6
    if tcd.step("1.Open new terminals to open all VMs"):
        # 1.Open new terminals to open all VMs
        # ssh -p 2201 localhost
        # ssh -p 2202 localhost
        # ...
        # ...
        
        # Login all VMs:
        # 2.Check Linux command line.
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -n 64 -c "python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on no5lvl\'"', timeout=10*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Login VM successfully")
        tcd.log("# ssh -p 2201 localhost")
        tcd.log("Kernel Parameters in guest:")
        tcd.log("intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce")
        ### Notes ###
        # Kernel 5.15+:
        # intel_iommu=on,sm_on no5lvl
        ##################
        
        
    ## 7
    if tcd.step("Run dmatest ."):
        # Run dmatest .
        # cd /root/accel-random-config-and-test/
        # modprbe idxd_ktest   ## Only for intel next kernel 5.12
        # ./Guest_Mdev_Randomize_IAX_Conf.sh -u
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/lnx_exec_with_check.py -c \'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && ./Guest_Mdev_Randomize_IAX_Conf.sh -u\' -m \'keyword\' -l \'enabled 1 wq(s) out of 1\'" -n 64', timeout=20*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Kernel type work-queues configured in virtual machines.")
        tcd.log("#./Guest_Mdev_Randomize_IAX_Conf.sh -u")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling work-queues:")
        tcd.log("iax0/wq0.0")
        tcd.log("enabled 1 wq(s) out of 1")
        tcd.log("...")
        ##################
        
        
    ## 8
    if tcd.step("Run dsa_test"):
        # Run dsa_test
        #./Guest_Mdev_Randomize_IAX_Conf.sh -r
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/lnx_exec_with_check.py -c \'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && ./Guest_Mdev_Randomize_IAX_Conf.sh -r\' -m \'keyword\' -l \'24 of 24 tests passed\'" -n 64', timeout=20*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("dmatest runs on each virtual machine without errors.")
        tcd.log("Logs show dmatest completed successfully on each thread.")
        tcd.log("#./Guest_Mdev_Randomize_IAX_Conf.sh -r")
        tcd.log("Running iax_test with # of WQs: 1")
        tcd.log("Using tests:    ./iaxbin/crc64 ./iaxbin/crc64_noInvert ./iaxbin/post_compress ./iaxbin/post_decompress ./iaxbin/post_de_scan ./iaxbin/post_expand ./iaxbin/post_expand1 ./iaxbin/post_extract ./iaxbin/post_extract1 ./iaxbin/post_find ./iaxbin/post_find1 ./iaxbin/post_rle ./iaxbin/post_rle1 ./iaxbin/post_scan ./iaxbin/post_select ./iaxbin/post_select1 ./iaxbin/post_set ./iaxbin/post_set1 ./iaxbin/test_compress ./iaxbin/test_decompress ./iaxbin/zcompress16 ./iaxbin/zcompress32 ./iaxbin/zdecompress16 ./iaxbin/zdecompress32")
        tcd.log("24 of 24 tests passed")
        tcd.log("...")
        ##################
        
        
    ## 9
    if tcd.step("Shutdown virtual machines on Host"):
        # Shutdown virtual machines on Host
        # ./Setup_Mdev_Multi_VM_DSA_IAX.sh -s
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "shutdown now" -n 64', no_check=True, timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Virtual machines shutdown")
        tcd.log("#./Setup_Mdev_Multi_VM_DSA_IAX.sh -s")
        tcd.log("Shutting down VMs...")
        tcd.log("Executing shutdown now on VM using port 2201...")
        tcd.log("root@localhost\'s password:")
        tcd.log("Connection to localhost closed by remote host.")
        tcd.log("...")
        tcd.log("...")
        ##################
        
        
    ## 10
    if tcd.step("Verify no errors in host dmesg"):
        # Verify no errors in host dmesg
        # dmesg
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py -i \'QAT: Failed to enable AER, error code -5,Record Serialization Table (ERST) support is initialized\'')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No errors reported")
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
