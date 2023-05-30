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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010639724
    #TITLE: IAX_TestFlow_reconfig_remove_reinsert_idxd_L
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
        
        
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # 1.Kernel parameters in host:
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
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        # 2.
        # cp or git clone accel-random-config-and-test to /root/DSA
        
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Change to PV DSA IAX Test Directory."):
        pass
        # Change to PV DSA IAX Test Directory.
        # cd /root/DSA/accel-random-config-and-test
        ##################
        
        
    ## 2
    if tcd.step("1.Configure work-queues:"):
        # 1.Configure work-queues:
        # ./Setup_Randomize_IAX_Conf.sh -a
        
        # 2.Verify no errors in dmesg:
        # dmesg
        
        # 3.Verify devices enabled:
        # accel-config list
        
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c "Setup_Randomize_IAX_Conf.sh -a"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"accel_config_check.py -a "iax"', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("All IAX devices configured.")
        tcd.log("All WQs configured")
        tcd.log("Script output shows wq(s) enabled.")
        tcd.log("# ./Setup_Randomize_IAX_Conf.sh -a")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("iax3 iax5 iax7 iax1")
        tcd.log("enabled 4 device(s) out of 4")
        tcd.log("Enabling work-queues:")
        tcd.log("iax3/wq3.7 iax3/wq3.5 iax3/wq3.3 iax3/wq3.4 iax3/wq3.6 iax3/wq3.0 iax3/wq3.2 iax3/wq3.1 iax5/wq5.5 iax5/wq5.7 iax5/wq5.2 iax5/wq5.0 iax5/wq5.3 iax5/wq5.4 iax5/wq5.1 iax5/wq5.6 iax7/wq7.7 iax7/wq7.4 iax7/wq7.2 iax7/wq7.1 iax7/wq7.3 iax7/wq7.5 iax7/wq7.0 iax7/wq7.6 iax1/wq1.2 iax1/wq1.5 iax1/wq1.3 iax1/wq1.7 iax1/wq1.1 iax1/wq1.0 iax1/wq1.4 iax1/wq1.6")
        tcd.log("enabled 32 wq(s) out of 32")
        tcd.log("Check logs in /root/spr-accelerators-random-config-and-test-master/logs/IAX_Configuration-20220127-132413")
        tcd.log("No errors in dmesg")
        tcd.log("# accel-config list")
        tcd.log("[")
        tcd.log("{")
        tcd.log("\"dev\":\"iax1\",")
        tcd.log("\"max_groups\":4,")
        tcd.log("\"max_work_queues\":8,")
        tcd.log("\"max_engines\":8,")
        tcd.log("\"work_queue_size\":128,")
        tcd.log("\"numa_node\":0,")
        tcd.log("\"op_cap\":[")
        tcd.log("\"0xd\",")
        tcd.log("\"0x7f331c\",")
        tcd.log("\"0\",")
        tcd.log("\"0\"")
        tcd.log("],")
        tcd.log("\"gen_cap\":\"0x71f10901f0105\",")
        tcd.log("\"version\":\"0x100\",")
        tcd.log("\"state\":\"enabled\",")
        tcd.log("\"max_batch_size\":1,")
        tcd.log("\"ims_size\":2048,")
        tcd.log("\"max_transfer_size\":2147483648,")
        tcd.log("\"configurable\":1,")
        tcd.log("\"pasid_enabled\":1,")
        tcd.log("\"cdev_major\":234,")
        tcd.log("\"clients\":0,")
        tcd.log("\"groups\":[")
        tcd.log("{")
        tcd.log("...")
        tcd.log("...")
        tcd.log("\"threshold\":0,")
        tcd.log("\"ats_disable\":0,")
        tcd.log("\"state\":\"enabled\",")
        tcd.log("\"clients\":0")
        tcd.log("}")
        tcd.log("],")
        tcd.log("\"grouped_engines\":[")
        tcd.log("{")
        tcd.log("\"dev\":\"engine7.0\",")
        tcd.log("\"group_id\":3")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine7.3\",")
        tcd.log("\"group_id\":3")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine7.5\",")
        tcd.log("\"group_id\":3")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine7.7\",")
        tcd.log("\"group_id\":3")
        tcd.log("}")
        tcd.log("]")
        tcd.log("}")
        tcd.log("]")
        tcd.log("}")
        tcd.log("]")
        ##################
        
        
    ## 3
    if tcd.step("1.NeRemove idxd kernel module:"):
        # 1.NeRemove idxd kernel module:
        # rmmod iax_crypto idxd_mdev idxd
        
        # 2.Verify idxd removed:
        # lsmod | grep idxd
        
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && rmmod iax_crypto idxd_mdev idxd')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'lsmod | grep idxd\' -m "no_found" -l \'idxd_mdev,iax_crypto,idxd\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("idxd kernel module removed")
        ##################
        
        
    ## 4
    if tcd.step("1.Insert idxd"):
        # 1.Insert idxd
        # modprobe idxd
        
        # 2.Verify idxd loaded:
        # lsmod | grep idxd
        
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && modprobe idxd')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'lsmod | grep idxd\' -m "keyword" -l \'idxd_mdev,iax_crypto,idxd\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("idxd module loaded")
        tcd.log("# lsmod | grep idxd")
        tcd.log("idxd_mdev              57344  0")
        tcd.log("idxd                  114688  2 iax_crypto,idxd_mdev")
        tcd.log("vfio_pci               81920  2 idxd,idxd_mdev")
        tcd.log("irqbypass              16384  3 idxd_mdev,vfio_pci,kvm")
        ##################
        
        
    ## 5
    if tcd.step("1.Configure work-queues:"):
        # 1.Configure work-queues:
        # ./Setup_Randomize_IAX_Conf.sh -a
        
        # 2.Verify no errors in dmesg:
        # dmesg
        
        # 3.Verify devices enabled:
        # accel-config list
        
        ### Call TCDB accel.iax_random_test Start
        sutos.execute_cmd(sut, f'dmesg -c')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c "Setup_Randomize_IAX_Conf.sh -a"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'dmesg -c')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/disable_device_conf.py -a IAX')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        ### Call TCDB accel.iax_random_test End
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("All IAX devices configured.")
        tcd.log("All WQs configured.")
        tcd.log("# ./Setup_Randomize_DSA_Conf.sh -a")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("dsa4 dsa0 dsa2 dsa6")
        tcd.log("enabled 4 device(s) out of 4")
        tcd.log("Enabling work-queues:")
        tcd.log("dsa4/wq4.4 dsa4/wq4.3 dsa4/wq4.2 dsa4/wq4.7 dsa4/wq4.5 dsa4/wq4.0 dsa4/wq4.1 dsa4/wq4.6 dsa0/wq0.7 dsa0/wq0.5 dsa0/wq0.3 dsa0/wq0.0 dsa0/wq0.6 dsa0/wq0.4 dsa0/wq0.2 dsa0/wq0.1 dsa2/wq2.3 dsa2/wq2.4 dsa2/wq2.7 dsa2/wq2.0 dsa2/wq2.1 dsa2/wq2.2 dsa2/wq2.5 dsa2/wq2.6 dsa6/wq6.0 dsa6/wq6.7 dsa6/wq6.6 dsa6/wq6.5 dsa6/wq6.2 dsa6/wq6.1 dsa6/wq6.3 dsa6/wq6.4")
        tcd.log("enabled 32 wq(s) out of 32")
        tcd.log("Check logs in /root/spr-accelerators-random-config-and-test-master/logs/DSA_Configuration-20220127-133326")
        tcd.log("No errors in dmesg")
        tcd.log("# accel-config list")
        tcd.log("[")
        tcd.log("{")
        tcd.log("\"dev\":\"dsa0\",")
        tcd.log("\"token_limit\":0,")
        tcd.log("\"max_groups\":4,")
        tcd.log("\"max_work_queues\":8,")
        tcd.log("\"max_engines\":4,")
        tcd.log("\"work_queue_size\":128,")
        tcd.log("\"numa_node\":0,")
        tcd.log("\"op_cap\":[")
        tcd.log("\"0x1003f03ff\",")
        tcd.log("\"0\",")
        tcd.log("\"0\",")
        tcd.log("\"0\"")
        tcd.log("],")
        tcd.log("\"gen_cap\":\"0x40915f010f\",")
        tcd.log("\"version\":\"0x100\",")
        tcd.log("\"state\":\"enabled\",")
        tcd.log("\"max_tokens\":96,")
        tcd.log("\"max_batch_size\":1024,")
        tcd.log("\"ims_size\":2048,")
        tcd.log("\"max_transfer_size\":2147483648,")
        tcd.log("\"configurable\":1,")
        tcd.log("\"pasid_enabled\":1,")
        tcd.log("\"cdev_major\":235,")
        tcd.log("...")
        tcd.log("...")
        tcd.log("\"name\":\"wq6.7\",")
        tcd.log("\"threshold\":16,")
        tcd.log("\"ats_disable\":0,")
        tcd.log("\"state\":\"enabled\",")
        tcd.log("\"clients\":0")
        tcd.log("}")
        tcd.log("],")
        tcd.log("\"grouped_engines\":[")
        tcd.log("{")
        tcd.log("\"dev\":\"engine6.0\",")
        tcd.log("\"group_id\":3")
        tcd.log("}")
        tcd.log("]")
        tcd.log("}")
        tcd.log("]")
        tcd.log("}")
        tcd.log("]")
        ##################
        
        
    ## 6
    if tcd.step("1.Disable all work-queues:"):
        # 1.Disable all work-queues:
        # ./Setup_Randomize_IAX_Conf.sh -d
        
        # 2.Check DMESG:
        # dmesg
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No failures in dmesg.")
        ##################
        
        
    ## 7
    if tcd.step("Repeat steps 2-4"):
        # Repeat steps 2-4
        
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c "Setup_Randomize_IAX_Conf.sh -a"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && rmmod iax_crypto idxd_mdev idxd')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c \'lsmod | grep idxd\' -m "no_found" -l \'idxd_mdev,iax_crypto,idxd\'')
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && modprobe idxd')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c \'lsmod | grep idxd\' -m "keyword" -l \'idxd_mdev,iax_crypto,idxd\'')
        
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
