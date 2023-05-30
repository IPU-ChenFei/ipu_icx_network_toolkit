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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010691567
    #TITLE: Stability_Idle_L
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
        sutos.execute_cmd(sut, f'ipmitool sel clear')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 5
    if tcd.step("5"):
        tcd.sleep(720)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No system reboot, no system hang,  no error reports")
        ### Notes ###
        # Wait for 12hours.
        ##################
        
        
    ## 6
    if tcd.step("6"):
        sutos.execute_cmd(sut, f'cat /var/log/message |grep -iE "Error|Fail|Failed"  -c | grep -E "^0$"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 7
    if tcd.step("7"):
        sutos.execute_cmd(sut, f'python check_bmc_sel.py', timeout=180)
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
