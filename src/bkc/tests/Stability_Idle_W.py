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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/1509775044
    #TITLE: Stability_Idle_W
    #DOMAIN: system
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Dependencies: Run all the pre-condition setup steps in the READMETK.md file on GitHub
        # Hardware Description: BKC HW Config #XXX
        # Software Description:  BKC #YY,
        # OS Limitation: Windows
        ## Boot to Windows
        tcd.os = "Windows"
        tcd.environment = "OS"
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("1"):
        sutos.execute_cmd(sut, f'Powershell -Command "& {{ Clear-EventLog -LogName System}}"', timeout=1800)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # N/A
        ##################
        
        
    ## 2
    if tcd.step("2"):
        tcd.execute_host_cmd(f'C:\\BKCPkg\\ipmitoolkit_1.8.18\\ipmitool.exe  -I lanplus -H {bmc.ipaddr} -U {bmc.username} -P {bmc.password} sel clear', timeout=180)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 3
    if tcd.step("3"):
        tcd.sleep(12*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No system reboot, no system hang,  no error reports")
        ### Notes ###
        # Wait for 12hours.
        ##################
        
        
    ## 4
    if tcd.step("4"):
        sutos.execute_cmd(sut, f'Powershell -Command "& {{Get-WinEvent -LogName system }}" > system_event.log', timeout=180)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # N/A
        ##################
        
        
    ## 5
    if tcd.step("5"):
        sutos.execute_cmd(sut, f'type system_event.log', timeout=180)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
        ### Notes ###
        # New
        ##################
        
        
    ## 6
    if tcd.step("6"):
        tcd.execute_host_cmd(f'C:\\BKCPkg\\ipmitoolkit_1.8.18\\ipmitool.exe  -I lanplus -H {bmc.ipaddr} -U {bmc.username} -P {bmc.password} sel list>C:\\BKCPkg\\ipmitoolkit_1.8.18\\bmc_sel_after_idle.log', timeout=180)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 7
    if tcd.step("7"):
        tcd.execute_host_cmd(f'type  C:\\BKCPkg\\ipmitoolkit_1.8.18\\bmc_sel_after_idle.log', timeout=60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No error reports")
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
