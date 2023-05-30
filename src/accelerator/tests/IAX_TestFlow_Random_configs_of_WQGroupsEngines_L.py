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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010629199
    #TITLE: IAX_TestFlow_Random_configs_of_WQ/Groups/Engines_L
    #DOMAIN: accelerator
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # 1. Follow Test Case below first:
        # DSA_Lib_install_L:https://hsdes.intel.com/appstore/article/#/1509782527
        # 2.set feature in kernel "intel_iommu=on,sm_on,iova_sl  idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
        # For intel next kernel 5.15 or newer ,
        # '
        # idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce
        # '
        # is no longer needed
        #
        # grubby --args="intel_iommu=on,sm_on,iova_sl idxd.dyndbg idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce
        # " --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+serv
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
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        # 3. cp or git clone accel-random-config-and-test to /root/DSA
        
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        sutos.execute_cmd(sut, f'mkdir -p $ACCE_RANDOM_CONFIG_PATH_L')
        sutos.execute_cmd(sut, f'unzip -o $ACCE_RANDOM_CONFIG_NAME -d $ACCE_RANDOM_CONFIG_PATH_L')
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Clean dmesg log"):
        # Clean dmesg log
        #dmesg -C
        sutos.execute_cmd(sut, f'dmesg -C')
        # Configure work-queues:
        #cd /roo/DSA/accel-random-config-and-test
        #./Setup_Randomize_IAX_Conf.sh -a
        
        
        # Verify no errors in dmesg:
        #dmesg
        
        
        # Verify devices enabled:
        # accel-config list
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No failures in dmesg.")
        tcd.log("accel-config JSON output shows all devices configured.")
        tcd.log("#./Setup_Randomize_IAX_Conf.sh -a")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("iax3 iax9 iax7 iax5 iax13 iax15 iax1 iax11")
        tcd.log("enabled 8 device(s) out of 8")
        tcd.log("Enabling work-queues:")
        tcd.log("iax3/wq3.0 iax3/wq3.3 iax3/wq3.7 iax3/wq3.1 iax3/wq3.4 iax3/wq3.6 iax3/wq3.5 iax3/wq3.2 iax9/wq9.0 iax9/wq9.7 iax9/wq9.4 iax9/wq9.6 iax9/wq9.2 iax9/wq9.3 iax9/wq9.5 iax9/wq9.1 iax7/wq7.6 iax7/wq7.4 iax7/wq7.1 iax7/wq7.7 iax7/wq7.3 iax7/wq7.2 iax7/wq7.5 iax7/wq7.0 iax5/wq5.6 iax5/wq5.1 iax5/wq5.0 iax5/wq5.5 iax5/wq5.4 iax5/wq5.3 iax5/wq5.2 iax5/wq5.7 iax13/wq13.0 iax13/wq13.2 iax13/wq13.5 iax13/wq13.7 iax13/wq13.4 iax13/wq13.1 iax13/wq13.3 iax13/wq13.6 iax15/wq15.0 iax15/wq15.3 iax15/wq15.2 iax15/wq15.6 iax15/wq15.5 iax15/wq15.1 iax15/wq15.4 iax15/wq15.7 iax1/wq1.3 iax1/wq1.7 iax1/wq1.0 iax1/wq1.5 iax1/wq1.4 iax1/wq1.1 iax1/wq1.2 iax1/wq1.6 iax11/wq11.2 iax11/wq11.7 iax11/wq11.0 iax11/wq11.5 iax11/wq11.4 iax11/wq11.1 iax11/wq11.6 iax11/wq11.3")
        tcd.log("enabled 64 wq(s) out of 64")
        tcd.log("Check logs in /root/jiejie/spr-accelerators-random-config-and-test-master/logs/IAX_Configuration-20220311-150238")
        ##################
        
        
    ## 2
    if tcd.step("Disable all work-queues:"):
        # Disable all work-queues:
        # ./Setup_Randomize_IAX_Conf.sh -d
        
        
        # Verify no errors in dmesg:
        # dmesg
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
        tcd.log("#./Setup_Randomize_IAX_Conf.sh -d")
        tcd.log("...")
        tcd.log("disabled 1 device(s) out of 1   iax5")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.0")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.1")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.2")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.3")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.4")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.5")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.6")
        tcd.log("disabled 1 wq(s) out of 1       iax7/wq7.7")
        tcd.log("disabled 1 device(s) out of 1   iax7")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.0")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.1")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.2")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.3")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.4")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.5")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.6")
        tcd.log("disabled 1 wq(s) out of 1       iax9/wq9.7")
        tcd.log("disabled 1 device(s) out of 1   iax9")
        ##################
        
        
    ## 3
    if tcd.step("Repeat steps 1 and 2 for 3 times ."):
        # Repeat steps 1 and 2 for 3 times .
        ### Call TCDB accel.iax_random_test Start
        sutos.execute_cmd(sut, f'dmesg -c')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c "Setup_Randomize_IAX_Conf.sh -a"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'dmesg -c')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/disable_device_conf.py -a IAX')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        ### Call TCDB accel.iax_random_test End
        
        
        ### Call TCDB accel.iax_random_test Start
        sutos.execute_cmd(sut, f'dmesg -c')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c "Setup_Randomize_IAX_Conf.sh -a"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'dmesg -c')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/disable_device_conf.py -a IAX')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        ### Call TCDB accel.iax_random_test End
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("repeat successfully")
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
