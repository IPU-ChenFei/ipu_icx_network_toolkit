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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011069251
    #TITLE: IAX passthrough with Guest VM
    #DOMAIN: accelerator
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Configuration:
        # https://hsdes.intel.com/appstore/article/#/15010469226
        # 1. Prepare BIOS setup
        # Ensure VT-d is enabled in BIOS. EDKII -> Socket Configuration -> IIO Configuration -> Intel VT for Directed I/O (VT-d) -> Intel VT for Directed I/O -> Enable
        # EDKII -> Socket Configuration -> IIO Configuration -> Intel VT for Directed I/O (VT-d) -> Interrupt Remapping -> Enable
        # EDKII Menu ->Socket Configuration -> IIO Configuration -> PCIe ENQCMD /ENQCMDS -> Yes
        # EDKII Menu -> Socket Configuration ->Processor Configuration -> VMX -> Enable
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
        
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 2.
        # cp or git clone accel-random-config-and-test to /root/DSA
        
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        # 3 Dependency
        #yum groupinstall -y "Development Tools"
        #yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools
        #yum install -y asciidoc xmlto libuuid-devel json-c-devel kmod-devel libudev-devel
        sutos.execute_cmd(sut, f'yum groupinstall -y "Development Tools"', timeout=10*60)
        sutos.execute_cmd(sut, f'yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools', timeout=10*60)
        sutos.execute_cmd(sut, f'yum install -y asciidoc xmlto libuuid-devel json-c-devel kmod-devel libudev-devel', timeout=10*60)
        # 4.VM test need copy OVMF.fd and ISO files to system.
        # centos image copy to/home/centos-8.4.2105-embargo-installer-202107220257.iso
        # OVMF file copy to /home/OVMF.fd
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -d \'iax\' -s \'1\' -g \'1\' -f $CENTOS_IMG_NAME -p \'1\'', timeout=10*60)
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/', timeout=10*60)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Update the kernel cmdline with \"intel_iommu=on,sm_on iommu=on no5lvl\" parameters"):
        # Update the kernel cmdline with "intel_iommu=on,sm_on iommu=on no5lvl" parameters
        # For intel next kernel 5.15 or newer , 'idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce'  is no longer needed
        # grubby --args="intel_iommu=on,sm_on,iova_sl  idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce no5lvl" --update-kernel=/boot/vmlinuz-5.12.0-0507.intel_next.06_30_po.13.x86_64+server
        
        # Reboot the system
        #reboot
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on iommu=on no5lvl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on iommu=on no5lvl\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("System should Restart successfully. Verify the cmdline whether the parameters are added or not.")
        tcd.log("# cat /proc/cmdline")
        tcd.log("Output:")
        tcd.log("BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.06_30_po.13.x86_64+server root=/dev/mapper/cl_r30s04-root ro crashkernel=auto resume=/dev/mapper/cl_r30s04-swap rd.lvm.lv=cl_r30s04/root rd.lvm.lv=cl_r30s04/swap rhgb console=tty0 console=ttyS0,115200n8 earlyprintk=ttyS0,115200 intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce no5lvl")
        ### Notes ###
        # Please use the grubby command with the kernel version that is used.
        ##################
        
        
    ## 2
    if tcd.step("Unbind the IAX Device and Launch VM with the DS device"):
        # Unbind the IAX Device and Launch VM with the DS device
        # lspci | grep 0cfe
        # modprobe vfio
        # modprobe vfio-pci
        # echo 0000:6a:02.0 > /sys/bus/pci/devices/0000:6a:02.0/driver/unbind
        # echo 8086 0cfe > /sys/bus/pci/drivers/vfio-pci/new_id
        
        
        #qemu-system-x86_64 -name guestVM1 -machine q35 -accel kvm -m 4096 -smp 4 -cpu host -monitor pty -drive format=raw,file=/home/qemu_centos_12.qcow2 -bios /home/OVMF.fd -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode="modern",device-iotlb=on,aw-bits=48 -device vfio-pci,host=6a:02.0 -nographic
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/passthrough.py -d iax -n 1 -g 1', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("\"lspci | grep 0cfe\" will listout the avaliable devices on the system")
        tcd.log("# lspci | grep 0cfe")
        tcd.log("e7:02.0 System peripheral: Intel Corporation Device 0cfe")
        tcd.log("ec:02.0 System peripheral: Intel Corporation Device 0cfe")
        tcd.log("f1:02.0 System peripheral: Intel Corporation Device 0cfe")
        tcd.log("f6:02.0 System peripheral: Intel Corporation Device 0cfe")
        tcd.log("VM should launch successfully without any errors")
        ##################
        
        
    ## 3
    if tcd.step("ssh login to host and VM"):
        # ssh login to host and VM
        # ssh root@hostip
        # ssh root@localhost -p 2222
        # Inside VM:
        
        # Check if the all the DSA MDEV devices attached to VM.
        # lspci | grep 0cfe
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c \'lspci | grep 0cfe\' -m \'keyword\' -l \'Intel Corporation Device\'"')
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Check if the all the DSA MDEV devices attached to VM by running \"lspci | grep 0b25\" command. This should list out the devices as follows. The number of devices shown should be same as the number of devices attached to the VM.")
        tcd.log("# lspci | grep 0b25")
        tcd.log("00:04.0 System peripheral: Intel Corporation Device 0cfe")
        ##################
        
        
    ## 4
    if tcd.step("Inside VM, Update the kernel cmdline with \"intel_iommu=on,sm_on iommu=on no5lvl\" parameters"):
        # Inside VM, Update the kernel cmdline with "intel_iommu=on,sm_on iommu=on no5lvl" parameters
        
        # grubby --args="intel_iommu=on,sm_on iommu=on no5lvl" --update-kernel=/boot/vmlinuz-5.12.0-0507.intel_next.06_30_po.13.x86_64+server
        
        
        # reboot
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on iommu=on no5lvl\'"')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "reboot"')
        tcd.sleep(120)
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DSA_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum groupinstall -y \'Development Tools\'"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y asciidoc xmlto libuuid-devel json-c-devel"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_install.py"', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("VM should Restart successfully. Verify the cmdline whether the parameters are added or not.")
        tcd.log("# cat /proc/cmdline")
        tcd.log("Output:")
        tcd.log("BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.06_30_po.13.x86_64+server root=/dev/mapper/cl_r30s04-root ro crashkernel=auto resume=/dev/mapper/cl_r30s04-swap rd.lvm.lv=cl_r30s04/root rd.lvm.lv=cl_r30s04/swap rhgb console=tty0 console=ttyS0,115200n8 earlyprintk=ttyS0,115200 intel_iommu=on,sm_on iommu=on no5lvl")
        ### Notes ###
        # Please use the grubby command with the kernel version that is used.
        ##################
        
        
    ## 5
    if tcd.step("login to VM"):
        # login to VM
        #ssh root@localhost -p 2222
        ##################
        tcd.log("### Expected result ###")
        tcd.log("login successfully")
        ##################
        
        
    ## 6
    if tcd.step("Inside VM, Download DSA/IAX random config scripts,"):
        # Inside VM, Download DSA/IAX random config scripts,
        #cd /root
        #sftp host_ip_address
        # > get -r /root/accel-random-config-and-test
        # > bye
        # cd accel-random-config-and-test/
        
        # Inside VM, Configure all IAX devices with user type work-queues and run IAX test
        # ./Setup_Randomize_IAX_Conf.sh  -ua
        # ./Setup_Randomize_IAX_Conf.sh  -r
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$ACCE_RANDOM_CONFIG_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c \'./Setup_Randomize_IAX_Conf.sh -ua\' -m guest -n 1"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c \'./Setup_Randomize_IAX_Conf.sh -r\'"', timeout=10*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("IAX Tests should run successfully without any errors in VM.")
        tcd.log("IAX device and wq enable success.")
        tcd.log("#./Setup_Randomize_IAX_Conf.sh -ua")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("iax0")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("Enabling work-queues:")
        tcd.log("iax0/wq0.5 iax0/wq0.4 iax0/wq0.6 iax0/wq0.2 iax0/wq0.3 iax0/wq0.0 iax0/wq0.1 iax0/wq0.7")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("....")
        tcd.log("# ./Setup_Randomize_IAX_Conf.sh -r")
        tcd.log("Running iax_test with # of WQs: 8")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Waiting for tests to finish..")
        tcd.log("192 of 192 tests passed")
        tcd.log("...")
        tcd.log("...")
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
