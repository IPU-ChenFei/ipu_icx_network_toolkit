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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010894622
    #TITLE: DSA_Stability_PCIe_Remove_Rescan_L
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
        
        
        sutos.execute_cmd(sut, f'dmesg -C')
        
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # 1. Use current BKC OS
        # 2.
        # cp or git clone accel-random-config-and-test to /root/DSA
        
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        # 3. Kernel parameters:
        # grubby --args="intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        #Note:
        # For intel next kernel 5.15 or newer ,
        # idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce
        # is no longer needed
        sutos.execute_cmd(sut, f'rm -rf $ACCE_RANDOM_CONFIG_PATH_L')
        sutos.execute_cmd(sut, f'mkdir -p $ACCE_RANDOM_CONFIG_PATH_L')
        sutos.execute_cmd(sut, f'unzip -o $ACCE_RANDOM_CONFIG_NAME -d $ACCE_RANDOM_CONFIG_PATH_L')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("in OS Prompt: do"):
        # in OS Prompt: do
        #lspci | grep 0b25
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on,iova_sl\'')
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
        tcd.log("f6:01.0 System peripheral: Intel Corporation Device 0b25")
        ##################
        
        
    ## 2
    if tcd.step("Run Script"):
        # Run Script
        
        # 1.Change to script directory.
        #cd /root/dsa/accel-random-config-and-test/accelerator_reset/
        
        # 2.Clean up dmesg log
        # dmesg -C
        
        # 3.Run Script
        #./pci_remove_rescan.sh -n <number of iterations>
        
        
        # Note: replace <number of iterations> with number of iterations from your testing plan.
        
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'python3 $API_SCRIPT/lnx_exec_with_check.py -c "./pci_remove_rescan.sh -n 10" -m "keyword" -l "Test Complete!" -d "$ACCE_RANDOM_CONFIG_PATH_L/accel-random-config-and-test-main/accelerator_reset/"', timeout=60*60)
        
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Script completes without errors.")
        tcd.log("No errors found. Test pass.")
        tcd.log("#./pci_remove_rescan.sh -n 10")
        tcd.log("Loop 1")
        tcd.log("removeing device 0000:6a:01.0")
        tcd.log("removeing device 0000:6f:01.0")
        tcd.log("removeing device 0000:74:01.0")
        tcd.log("removeing device 0000:79:01.0")
        tcd.log("removeing device 0000:e7:01.0")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Rescanning root port /sys/devices/pci0000:e7")
        tcd.log("Rescanning root port /sys/devices/pci0000:ec")
        tcd.log("Rescanning root port /sys/devices/pci0000:f1")
        tcd.log("Rescanning root port /sys/devices/pci0000:f6")
        tcd.log("Devices found after rescan: 8")
        tcd.log("Test Complete!")
        tcd.log("Check demsg for errors.")
        ##################
        
        
    ## 3
    if tcd.step("Check DMESG"):
        # Check DMESG
        
        # dmesg
        
        sutos.execute_cmd(sut, f'python3 $API_SCRIPT/dmesg_check.py')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("no unexpected errors found in dmesg.")
        tcd.log("# dmesg")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[  950.896397] idxd 0000:f6:01.0: IDXD Group Config Offset: 0x300")
        tcd.log("[  950.896398] idxd 0000:f6:01.0: IDXD Work Queue Config Offset: 0x400")
        tcd.log("[  950.896398] idxd 0000:f6:01.0: IDXD MSIX Permission Offset: 0x200")
        tcd.log("[  950.896399] idxd 0000:f6:01.0: IDXD Perfmon Offset: 0x1000")
        tcd.log("[  950.896400] idxd 0000:f6:01.0: IDXD IMS Offset: 0x4000")
        tcd.log("[  950.898661] idxd 0000:f6:01.0: Allocated idxd-misc handler on msix vector 300")
        tcd.log("[  950.900727] idxd 0000:f6:01.0: IDXD device 14 probed successfully")
        tcd.log("[  950.901031] idxd 0000:f6:01.0: Intel(R) Accelerator Device (v100)")
        ##################
        
        
    ## 4
    if tcd.step("4"):
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        sutos.execute_cmd(sut, f'rm -rf $ACCE_RANDOM_CONFIG_PATH_L')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("remove the driver and clean the kernel")
        ### Notes ###
        # For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce is no longer needed
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
