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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010691726
    #TITLE: Cold_reset_cycle_with_Sandstone_Test
    #DOMAIN: system
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Dependencies: Run all the pre-condition setup steps in the READMETK.md file on GitHub,
        # The sandstone cycles has several criterial: power on: 4h,  BKC : 12h,  Volume validation: 48h
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
        sutos.execute_cmd(sut, f'ipmitool sel clear', timeout=30)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 5
    if tcd.step("5"):
        sutos.execute_cmd(sut, f'echo "sandstone test start!" > /var/log/sandstone.log')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 6
    if tcd.step("## Call TCDB BKC_UNIQ_15010691726 Start"):
        
        ### Call TCDB BKC_UNIQ_15010691726 Start
        for i in range(0, 2):
            # Test Tcd
        
            sutos.execute_cmd(sut, f'systemctl daemon-reload')
            sutos.execute_cmd(sut, f'systemctl enable docker')
            sutos.execute_cmd(sut, f'systemctl start docker')
            sutos.execute_cmd(sut, f'docker run -i --privileged prt-registry.sova.intel.com/sandstone:95 -vv --beta -T 5m --disable=@locks_cross_cacheline >> /var/log/sandstone.log', timeout=15*60)
            sutos.execute_cmd(sut, f'echo "-------------cycle {i+1} done!----------------------" >> /var/log/sandstone.log')
            tcd.cold_reset()
            tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB BKC_UNIQ_15010691726 End
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # New
        ##################
        
        
    ## 7
    if tcd.step("7"):
        sutos.execute_cmd(sut, f'cat /var/log/sandstone.log')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 8
    if tcd.step("8"):
        sutos.execute_cmd(sut, f'cat /var/log/sandstone.log |grep -i "cycle 2 done" -c')
        ### Notes ###
        # New
        ##################
        
        
    ## 9
    if tcd.step("9"):
        sutos.execute_cmd(sut, f'cat /var/log/sandstone.log |grep -iE "Error|Fail|Failed" -c |grep -E "^0"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # New
        ##################
        
        
    ## 10
    if tcd.step("10"):
        sutos.execute_cmd(sut, f'python messages_check_with_white_list.py')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 11
    if tcd.step("11"):
        sutos.execute_cmd(sut, f'python check_bmc_sel.py', timeout=1800)
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
