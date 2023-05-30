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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010879052
    #TITLE: DSA_usermode_test_with_mdev_DPDK_L
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
        
        ## Set BIOS knob: ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("ProcessorX2apic=0x1, VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 1. Follow Test Case below first:
        # DSA_Lib_install_L:https://hsdes.intel.com/appstore/article/#/1509782527
        # 2.set feature in kernel "
        # intel_iommu=on,sm_on,iova_sl"
        # grubby --args=" intel_iommu=on,sm_on,iova_sl " --update-kernel=/boot/vmlinuz-*
        sutos.execute_cmd(sut, f'unzip -o $DPDK_DRIVER_BKC_ZIP_NAME', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # 3.Install dependency
        # dnf install meson
        #pip3 install pyelftools
        sutos.execute_cmd(sut, f'dnf -y install meson', timeout=20*60)
        sutos.execute_cmd(sut, f'pip3 install pyelftools --proxy=http://proxy-dmz.intel.com:912', timeout=20*60)
        sutos.execute_cmd(sut, f'dnf install -y python3 python3-pip python3-setuptools python3-wheel ninja-build', timeout=20*60)
        # 4.Download latest DPDK driver  from BKC release to /root/
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("check feature in kernel:"):
        # check feature in kernel:
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("make sure intel_iommu=on.sm_on is  set")
        tcd.log("# cat /proc/cmdline")
        tcd.log("BOOT_IMAGE=(hd0,gpt3)/vmlinuz-5.15.0-spr.bkc.pc.3.21.0.x86_64 root=/dev/mapper/cs_embargo-root ro crashkernel=auto resume=/dev/mapper/cs_embargo-swap rd.lvm.lv=cs_embargo/root rd.lvm.lv=cs_embargo/swap rhgb console=ttyS0,115200n8 console=tty0 intel_iommu=on,sm_on,iova_sl default_hugepagesz=1G hugepagesz=1G hugepages=16 intel_pstate=disable acpi_pad.disable=1")
        ##################
        
        
    ## 2
    if tcd.step("in OS Prompt: do"):
        # in OS Prompt: do
        # lspci | grep 0b25
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'lspci | grep 0b25\' -m "keyword" -l \'Intel Corporation Device\'')
        
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
        tcd.log("f6:01.0 System peripheral: Intel Corporation Device 0b25")
        ##################
        
        
    ## 3
    if tcd.step("In OS:"):
        # In OS:
        # cd /root/
        #unzip dpdk-<version>.zip
        # unxz dpdk-<version>.tar.xz
        # tar -xvf dpdk-<version>.tar
        #cd dpdk-<version>
        
        sutos.execute_cmd(sut, f'tar xfJ $DPDK_DRIVER_BKC_NAME -C $Accelerator_REMOTE_TOOL_PATH')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && rm -rf dpdk')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && mv dpdk-* dpdk')
        ### Notes ###
        # New
        ##################
        
        
    ## 4
    if tcd.step("Set hugepage"):
        # Set hugepage
        #echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
        
        sutos.execute_cmd(sut, f'echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error")
        ### Notes ###
        # New
        ##################
        
        
    ## 5
    if tcd.step("Build DPDK:"):
        # Build DPDK:
        # meson build
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'cd $Accelerator_REMOTE_TOOL_PATH/dpdk && meson build\' -m "no_found" -l \'error,Error,ERROR\'', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error when meson build")
        tcd.log("# meson build")
        tcd.log("The Meson build system")
        tcd.log("Version: 0.55.3")
        tcd.log("Source dir: /root/dpdk-21.11")
        tcd.log("Build dir: /root/dpdk-21.11/build")
        tcd.log("Build type: native build")
        tcd.log("Program cat found: YES")
        tcd.log("Project name: DPDK")
        tcd.log("Project version: 21.11.0")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Build targets in project: 942")
        tcd.log("Found ninja-1.8.2 at /usr/bin/ninja")
        ### Notes ###
        # New
        ##################
        
        
    ## 6
    if tcd.step("ninja -C build"):
        # ninja -C build
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'cd $Accelerator_REMOTE_TOOL_PATH/dpdk && ninja -C build\' -m "no_found" -l \'error,Error,ERROR\'', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Ninja build successful")
        tcd.log("# ninja -C build")
        tcd.log("ninja: Entering directory `build\'")
        tcd.log("[0/2686] Compiling C object lib/librte_kvargs.a.p/kvargs_rte_kvargs.c.o")
        tcd.log("[0/2686] Generating rte_kvargs_def with a custom command")
        tcd.log("[0/2686] Generating rte_kvargs_mingw with a custom command")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[2685/2686] Linking target app/dpdk-test-gpudev")
        tcd.log("[2686/2686] Linking target app/dpdk-test-regex")
        ##################
        
        
    ## 7
    if tcd.step("bind at least one DSA device to vfio-pci driver"):
        # bind at least one DSA device to vfio-pci driver
        #modprobe vfio-pci
        #./usertools/dpdk-devbind.py -b vfio-pci 6a:01.0
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/bind_device_pci.py -d dsa -n 1', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error")
        ##################
        
        
    ## 8
    if tcd.step("Run the unit test"):
        # Run the unit test
        #./build/app/test/dpdk-test -- dmadev_autotest
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'cd $Accelerator_REMOTE_TOOL_PATH/dpdk && ./build/app/test/dpdk-test -- dmadev_autotest\' -m \'keyword\' -l \'Test OK\'', timeout=60*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("the test result print out in terminal, if any error, report out")
        tcd.log("#./build/app/test/dpdk-test -- dmadev_autotest")
        tcd.log("EAL: Detected CPU lcores: 80")
        tcd.log("EAL: Detected NUMA nodes: 2")
        tcd.log("EAL: Detected static linkage of DPDK")
        tcd.log("EAL: Multi-process socket /var/run/dpdk/rte/mp_socket")
        tcd.log("...")
        tcd.log("...")
        tcd.log("### Test dmadev infrastructure using skeleton driver")
        tcd.log("test_dma_get_dev_id_by_name Passed")
        tcd.log("test_dma_is_valid_dev Passed")
        tcd.log("test_dma_count Passed")
        tcd.log("test_dma_info_get Passed")
        tcd.log("...")
        tcd.log("...")
        tcd.log("DMA Dev 0: device does not report errors, skipping error handling tests")
        tcd.log("DMA Dev 0: No device fill support, skipping fill tests")
        tcd.log("Test OK")
        ##################
        
        
    ## 9
    if tcd.step("9"):
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        sutos.execute_cmd(sut, f'rm -rf $Accelerator_REMOTE_TOOL_PATH/dpdk')
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
