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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010592432
    #TITLE: DSA_NUMA_CTL_test_L
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
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Install numactl package:"):
        #Install numactl package:
        # dnf install numactl
        
        sutos.execute_cmd(sut, f'dnf install numactl -y', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("numactl installed")
        ### Notes ###
        # New
        ##################
        
        
    ## 2
    if tcd.step("Run Test"):
        #Run Test
        #Note: it is expected that all dsa_devices are disabled before running test.
        
        
        #1. set path to dsa_test. note: this should be in the directory compiled in the previous step.
        #Note: This path is inside the cloned idxd_config repo.
        # export dsa_test=/usr/share/accel-config/test/dsa_test
        
        
        #2. copy attached script to /root/DSA and run it.
        # cd /root/DSA
        # chmod +x dsa_test_numactl.sh
        # ./dsa_test_numactl.sh
        
        ### Call TCDB accel.DSA_test Start
        sutos.execute_cmd(sut, f'rm -rf $DSA_PATH_L')
        sutos.execute_cmd(sut, f'mkdir -p $DSA_PATH_L')
        sutos.execute_cmd(sut, f'echo export dsa_test=/usr/share/accel-config/test/dsa_test >> $HOME/.bashrc')
        sutos.execute_cmd(sut, f'source $HOME/.bashrc')
        sutos.execute_cmd(sut, f'\cp $SUT_TOOLS/dsa_test_numactl.sh $DSA_PATH_L/dsa_test_numactl.sh')
        sutos.execute_cmd(sut, f'cd $DSA_PATH_L && chmod +x dsa_test_numactl.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -m "no_found" -c \'cd $DSA_PATH_L && ./dsa_test_numactl.sh\' -l "failed"')
        ### Call TCDB accel.DSA_test End
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("DSA devices configured without any errors.")
        tcd.log("Test is run without failures.")
        tcd.log("# ./dsa_test_numactl.sh")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[debug] umwait supported")
        tcd.log("[ info] alloc wq 7 shared 1 size 16 addr 0x7f3567e84000 batch sz 0x400 xfer sz 0x80000000")
        tcd.log("[ info] testmemory: opcode 3 len 0x200000 tflags 0x1 num_desc 1")
        tcd.log("[debug] initilizing single task 0x4133c0")
        tcd.log("[debug] Mem allocated: s1 0x7f356749d010 s2 0 d1 0x7f356729c000 d2 0")
        tcd.log("[ info] preparing descriptor for memcpy")
        tcd.log("[ info] Submitted all memcpy jobs")
        tcd.log("[debug] desc addr: 0x428f70")
        tcd.log("[debug] desc[0]: 0x0300000e00000000")
        tcd.log("[debug] desc[1]: 0x0000000000428fc0")
        tcd.log("[debug] desc[2]: 0x00007f356749d010")
        tcd.log("[debug] desc[3]: 0x00007f356729c000")
        tcd.log("[debug] desc[4]: 0x0000000000200000")
        tcd.log("[debug] desc[5]: 0x0000000000000000")
        tcd.log("[debug] desc[6]: 0x0000000000000000")
        tcd.log("[debug] desc[7]: 0x0000000000000000")
        tcd.log("[debug] completion record addr: 0x428fc0")
        tcd.log("[debug] compl[0]: 0x0000000000000001")
        tcd.log("[debug] compl[1]: 0x0000000000000000")
        tcd.log("[debug] compl[2]: 0x0000000000000000")
        tcd.log("[debug] compl[3]: 0x0000000000000000")
        tcd.log("[ info] verifying task result for 0x4133c0")
        tcd.log("real0m0.036s")
        tcd.log("user0m0.011s")
        tcd.log("sys0m0.010s")
        ##################
        
        
    ## 3
    if tcd.step("Check logfiles at logs/DSA_numactl-<date-time>"):
        #Check logfiles at logs/DSA_numactl-<date-time>
        
        
        #Verify that all logs show completition status of "1"
        #cd into logs/DSA_numactl-<date-time>
        #grep "compl\[0\]:" ./*
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -m "no_found" -c \'cd $DSA_PATH_L/logs/DSA_numactl-* && grep "compl\[0\]:" ./* \' -l "error, Error, ERROR"')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -m "kv" -c \'cd $DSA_PATH_L/logs/DSA_numactl-* && grep "compl\[0\]:" ./* \' -l "compl,0x0000000000000001"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Test completes without errors.")
        tcd.log("There should no failures or errors in log files.")
        tcd.log("all logs should show \"[debug] compl[0]: 0x0000000000000001\"")
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
