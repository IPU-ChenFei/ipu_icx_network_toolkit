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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/1509775119
    #TITLE: Stress_Bonnie++_FIO_L
    #DOMAIN: system
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Dependencies: Run all the pre-condition setup steps in the READMETK.md file on GitHub
        # Hardware Description: BKC HW Config #XXX
        # Software Description:  BKC #YY,
        # OS Limitation:  Linux
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Manual Steps:"):
        #Manual Steps:
        # go to the directory,excute the command:
        # "./bonnie++ -d /mnt -s 1000 -r 500 -u root > /var/log/bonnie.log"
        # -d:mean the directory which device mount on
        # -s:test file size
        # -r:memory size
        # The file size must be several times the size of the memory.
        # according to need change this parameter values
        #HLS Steps:
        sutos.execute_cmd(sut, f'python run_bonnie.py', timeout=1800)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 2
    if tcd.step("2"):
        tcd.sleep(5)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # wait 5 seconds
        ##################
        
        
    ## 3
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
