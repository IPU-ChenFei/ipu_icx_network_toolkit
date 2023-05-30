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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/1509775233
    #TITLE: Stress_Prime95_FIO_L
    #DOMAIN: system
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Dependencies: Run all the pre-condition setup steps in the READMETK.md file on GitHub,
        # The prime95 and FIO run time has several criterial: power on: 4h,  BKC : 12h,  Volume validation: 48h
        # Hardware Description: BKC HW Config #XXX
        # Software Description:  BKC #YY,
        # OS Limitation:  Linux
        ## Boot to Linux
        boot_to(sut, sut.default_os)
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("1"):
        sutos.execute_cmd(sut, f'python dmesg_check_with_white_list.py')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 2
    if tcd.step("2"):
        sutos.execute_cmd(sut, f'mv /var/log/messages /var/log/messages.bk')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 3
    if tcd.step("3"):
        sutos.execute_cmd(sut, f'systemctl restart syslog')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 4
    if tcd.step("4"):
        sutos.execute_cmd(sut, f'python3 BKC_UNIQ_prime95.py', timeout=18000)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # New
        ##################
        
        
    ## 5
    if tcd.step("5"):
        tcd.sleep(10)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # New
        ##################
        
        
    ## 6
    if tcd.step("6"):
        sutos.execute_cmd(sut, f'cat /opt/prime95/prime95.log')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 7
    if tcd.step("7"):
        sutos.execute_cmd(sut, f'cat /opt/prime95/prime95.log  |grep -i "Prime95 Test PASS!"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # New
        ##################
        
        
    ## 8
    if tcd.step("8"):
        tcd.sleep(10)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 9
    if tcd.step("Manual Steps:"):
        #Manual Steps:
        # use "100% random 70%read 30%write,every io block is 4k"this mode
        # test ,the command as below and can use"fio -help" for help,also can
        # according to your need change these parameter values
        
        # command: fio -filename=/dev/sda3 -direct=1 -iodepth 1 -thread
        # -rw=randrw -rwmixread=70 -ioengine=psync -bs=4k -size=300G
        # -numjobs=50 -runtime=180 -group_reporting -name=randrw_70read_4k
        
        #HLS Steps:
        sutos.execute_cmd(sut, f'python scan_free_disk_and_FIO.py', timeout=1800)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 10
    if tcd.step("10"):
        sutos.execute_cmd(sut, f'cat /var/log/message |grep -iE "Error|Fail|Failed"  -c | grep -E "^0$"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
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
