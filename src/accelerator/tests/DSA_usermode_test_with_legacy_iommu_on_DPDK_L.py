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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010876698
    #TITLE: DSA_usermode_test_with_legacy_iommu_on_DPDK_L
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
        
        
        sutos.execute_cmd(sut, f'unzip -o $DPDK_DRIVER_BKC_ZIP_NAME', timeout=10*60)
        
        ## Boot to Linux
        boot_to(sut, sut.default_os)
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        ## Set BIOS knob: ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 1.set feature in kernel "intel_iommu=on,sm_off  "
        # grubby --args="intel_iommu=on,sm_off  " --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+serv
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_off\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # 2. git  clone dpdk to /root
        # export http_proxy="http://proxy-dmz.intel.com:911"
        # export HTTP_PROXY="http://proxy-dmz.intel.com:911"
        # export https_proxy="http://proxy-dmz.intel.com:912"
        # export HTTP_PROXY="http://proxy-dmz.intel.com:912"
        # export no_proxy="120.0.0.1,localhost,intel.com"
        # export NO_PROXY="120.0.0.1,localhost,intel.com"
        # cd /root
        # git clone http://dpdk.org/git/dpdk
        sutos.execute_cmd(sut, f'tar xfJ $DPDK_DRIVER_BKC_NAME -C $Accelerator_REMOTE_TOOL_PATH', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && rm -rf dpdk', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && mv dpdk-* dpdk', timeout=10*60)
        # 2.Install dependency
        # pip3 install pyelftools or yum install python3-pyelftools
        # dnf install meson
        # dnf install  python3 python3-pip python3-setuptools python3-wheel ninja-build
        sutos.execute_cmd(sut, f'dnf install meson -y', timeout=10*60)
        sutos.execute_cmd(sut, f'dnf install python3 python3-pip python3-setuptools python3-wheel ninja-build -y', timeout=10*60)
        sutos.execute_cmd(sut, f'yum install python3-pyelftools -y', timeout=10*60)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("check feature in kernel:"):
        # check feature in kernel:
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_off\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("make sure intel_iommu=on.sm_off is  set")
        tcd.log("# cat /proc/cmdline")
        tcd.log("BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-intel-next.sprd0po.09022021+ root=/dev/mapper/cl_embargo-root ro crashkernel=auto resume=/dev/mapper/cl_embargo-swap rd.lvm.lv=cl_embargo/root rd.lvm.lv=cl_embargo/swap rhgb console=ttyS0,115200n8 console=tty0 intel_iommu=on,sm_off  idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce")
        ### Notes ###
        # For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce is no longer needed
        ##################
        
        
    ## 2
    if tcd.step("in OS Prompt: do"):
        # in OS Prompt: do
        #lspci | grep 0b25
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c "lspci | grep 0b25" -m "keyword" -l "Intel Corporation Device"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("it should show all the DSA in system.")
        tcd.log("# lspci |grep 0b25")
        tcd.log("6a:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("6f:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("74:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("79:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("e7:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("ec:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("f1:01.0 System peripheral: Intel Corporation Device 0b25")
        tcd.log("f6:01.0 System peripheral: Intel Corporation Device 0b2")
        ##################
        
        
    ## 3
    if tcd.step("Set hugepage"):
        # Set hugepage
        #echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c "echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages" -m "no_found" -l "error"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error")
        ##################
        
        
    ## 4
    if tcd.step("Build DPDK:"):
        # Build DPDK:
        #cd /root/dpdk
        #meson build
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'cd $Accelerator_REMOTE_TOOL_PATH/dpdk && meson build\' -m \'no_found\' -l \'error,Error,ERROR\'', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error when meson build")
        tcd.log("#meson build")
        tcd.log("...")
        tcd.log("Message:")
        tcd.log("=================")
        tcd.log("Content Skipped")
        tcd.log("=================")
        tcd.log("libs:")
        tcd.log("drivers:")
        tcd.log("common/mvep:    missing dependency, \"libmusdk\"")
        tcd.log("common/mlx5:    missing dependency, \"mlx5\"")
        tcd.log("net/af_xdp:     missing dependency, \"libxdp\" and \"libbpf\"")
        tcd.log("net/ipn3ke:     missing dependency, \"libfdt\"")
        tcd.log("net/mlx4:       missing dependency, \"mlx4\"")
        tcd.log("net/mlx5:       missing internal dependency, \"common_mlx5\"")
        tcd.log("net/mvneta:     missing dependency, \"libmusdk\"")
        tcd.log("net/mvpp2:      missing dependency, \"libmusdk\"")
        tcd.log("net/nfb:        missing dependency, \"libnfb\"")
        tcd.log("net/pcap:       missing dependency, \"libpcap\"")
        tcd.log("net/sfc:        broken dependency, \"libatomic\"")
        tcd.log("raw/ifpga:      missing dependency, \"libfdt\"")
        tcd.log("raw/ioat:       replaced by dmadev drivers")
        tcd.log("crypto/armv8:   missing dependency, \"libAArch64crypto\"")
        tcd.log("crypto/ipsec_mb:        missing dependency, \"libIPSec_MB\"")
        tcd.log("crypto/mlx5:    missing internal dependency, \"common_mlx5\"")
        tcd.log("crypto/mvsam:   missing dependency, \"libmusdk\"")
        tcd.log("compress/isal:  missing dependency, \"libisal\"")
        tcd.log("compress/mlx5:  missing internal dependency, \"common_mlx5\"")
        tcd.log("regex/mlx5:     missing internal dependency, \"common_mlx5\"")
        tcd.log("vdpa/mlx5:      missing internal dependency, \"common_mlx5\"")
        tcd.log("gpu/cuda:       missing dependency, \"cuda.h\"")
        tcd.log("Build targets in project: 1088")
        tcd.log("Found ninja-1.8.2 at /usr/bin/ninja")
        ##################
        
        
    ## 5
    if tcd.step("ninja -C build"):
        #ninja -C build
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'cd $Accelerator_REMOTE_TOOL_PATH/dpdk && ninja -C build\' -m "no_found" -l \'error,Error,ERROR\'', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Ninja build successful")
        tcd.log("#ninja -C build")
        tcd.log("ninja: Entering directory `build\'")
        tcd.log("[3323/3323] Linking target app/test/dpdk-test")
        ##################
        
        
    ## 6
    if tcd.step("bind at least one DSA device to vfio-pci driver"):
        # bind at least one DSA device to vfio-pci driver
        # modprobe vfio-pci
        #./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/bind_device_pci.py -d dsa -n 1')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error")
        ##################
        
        
    ## 7
    if tcd.step("Run the unit test"):
        # Run the unit test
        #./build/app/test/dpdk-test -- dmadev_autotest
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c "cd $Accelerator_REMOTE_TOOL_PATH/dpdk && ./build/app/test/dpdk-test -- dmadev_autotest" -m "keyword" -l "Test OK"', timeout=750)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("the test result print out in terminal, if any error, report out")
        tcd.log("#./build/app/test/dpdk-test -- dmadev_autotest")
        tcd.log("...")
        tcd.log("RTE>>dmadev_autotest")
        tcd.log("skeldma_probe(): Create dma_skeleton dmadev with lcore-id -1")
        tcd.log("### Test dmadev infrastructure using skeleton driver")
        tcd.log("test_dma_get_dev_id_by_name Passed")
        tcd.log("test_dma_is_valid_dev Passed")
        tcd.log("test_dma_count Passed")
        tcd.log("test_dma_info_get Passed")
        tcd.log("test_dma_configure Passed")
        tcd.log("test_dma_vchan_setup Passed")
        tcd.log("test_dma_start_stop Passed")
        tcd.log("test_dma_stats Passed")
        tcd.log("test_dma_dump Passed")
        tcd.log("test_dma_completed Passed")
        tcd.log("test_dma_completed_status Passed")
        tcd.log("Total tests   : 11")
        tcd.log("Passed        : 11")
        tcd.log("Failed        : 0")
        tcd.log("...")
        tcd.log("### Test dmadev instance 8 [dma_skeleton]")
        tcd.log("DMA Dev 8: Running copy Tests")
        tcd.log("Ops submitted: 85120    Ops completed: 85120    Errors: 0")
        tcd.log("DMA Dev 8: Running burst capacity Tests")
        tcd.log("Ops submitted: 65536    Ops completed: 65536    Errors: 0")
        tcd.log("DMA Dev 8: device does not report errors, skipping error handling tests")
        tcd.log("DMA Dev 8: No device fill support, skipping fill tests")
        tcd.log("Test OK")
        ##################
        
        
    ## 8
    if tcd.step("8"):
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_off\'')
        sutos.execute_cmd(sut, f'rm -rf $Accelerator_REMOTE_TOOL_PATH/dpdk')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("remove the driver and clean the kernel")
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
