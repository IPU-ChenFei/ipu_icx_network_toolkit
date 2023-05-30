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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010585504
    #TITLE: PI_Memory_SNC2_Check_Stressapp_L
    #DOMAIN: memory
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Hardware and Infrastructure Setup
        # BMC      is in interactive mode
        # Platform      should have POR memory config: 1DPC/2DPC
        # Ensure      covering DDR5 vendors: Hynix, Micron, Samsung
        # Platform      cooling fans running with 100% rpm to avoid CPU performance related issues      due to thermal events
        # Prepare Steps
        # SUT      booting into Linux with supported POR memory config:1DPC Or 2DPC
        ## Boot to Linux
        boot_to(sut, sut.default_os)
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # Enable      SNC :
        ## Set BIOS knob: SncEn=0x2
        set_cli = not sut.xmlcli_os.check_bios_knobs("SncEn=0x2")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("SncEn=0x2")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("SncEn=0x2"))
        
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("In OS, Check the dimm number :"):
        # In OS, Check the dimm number :
        sutos.execute_cmd(sut, f'dmidecode -t 17 | grep -E -v "No|Vo" | grep "Size" | nl')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("dimm number should be match with hardware configuration")
        ### Notes ###
        # Step 3
        ##################
        
        
    ## 2
    if tcd.step("In OS, Check the numa node:"):
        # In OS, Check the numa node:
        sutos.execute_cmd(sut, f'ls -d /sys/devices/system/node/node*')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Make sure that the numbers of nodes are as expected")
        tcd.log("SNC2 shoule be:number of sockets*2")
        ### Notes ###
        # Step 4
        ##################
        
        
    ## 3
    if tcd.step("pls install latest version of stressapptest-master, stress, and run below memory stress :"):
        # pls install latest version of stressapptest-master, stress, and run below memory stress :
        
        sutos.execute_cmd(sut, f'{tools.stressapp_l.ipath}/src/stressapptest -s 43200 -M -m -W', timeout=80*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("1)No hang or reboot")
        tcd.log("2)Test passed")
        ### Notes ###
        # Step 5
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
