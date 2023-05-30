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


    # Tool Version [0.2.11]
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/16015342566
    #TITLE: test with timestamp 2021-12-09, 14:44:48
    #DOMAIN: unclassified
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Pre_condition:
        # 1. Config your system following the test plan including HW config and SW config.
        # 2. Make sure ITP was connected to your system. Make sure <pythonsv> has updated to the latest and works well on the host.
        # 3. Connect "Bios Serial cable" to system. Open putty or taraterm for logging the log.
        # 4. Connect BMC Serial cable to system. Use &cmdtool to enable BMC console login account. Open putty or taraterm for logging the log.
        # Tools and Devices(HW --- SW)
        # 1.Blaster --- Quartus : For updating CPLD
        # 2.ITP --- Pythonsv : For save the log
        # 3. cmdtool: For enabling BMC console account
        # Prepare Steps:
        ## Boot to Windows
        boot_to(sut, sut.default_os)
        tcd.os = "Windows"
        tcd.environment = "OS"
        
        tcd.itplib = "pythonsv"
        ## Set BIOS knob: VTdSupport=0x0, ProcessorLtsxEnable=0x1, ProcessorSmxEnable=0x1, SecureBoot=Standard Mode, SncEn=0x0
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x0, ProcessorLtsxEnable=0x1, ProcessorSmxEnable=0x1, SncEn=0x0")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x0, ProcessorLtsxEnable=0x1, ProcessorSmxEnable=0x1, SncEn=0x0")
        sutos.reset_to_bios_menu(sut)
        changed_0 = sut.set_bios_knobs_menu(menu_knob_secureboot, "Standard Mode")
        if changed_0:
            BIOS_Menu.reset_cycle_step(sut)
            tcd.expect("SecureBoot/menu_knob_secureboot is Standard Mode", sut.check_bios_knobs_menu(menu_knob_secureboot, "Standard Mode"))
        BIOS_Menu.continue_to_os(sut)
        if set_cli:
            tcd.expect("double check", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x0, ProcessorLtsxEnable=0x1, ProcessorSmxEnable=0x1, SncEn=0x0"))
        
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # test for error condition
        # aaa Set Feature: Vtd, Enable
        # bbb ItpLib = cscript
        # ccc Wait for: OS
        # dddWait for: OS
        # eeeEnvironment=UEFI SHELL
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Run workloads"):
        # Run workloads
        
        sutos.execute_cmd(sut, f'/home/BKCPkg/domains/PM/mlc-linux/ipmitool sel clear, 200')
        sutos.execute_cmd(sut, f'cat /dev/null > /var/log/messages, 200')
        sutos.execute_cmd(sut, f'/home/BKCPkg/domains/PM/mlc-linux/mlc_internal --loaded_latency -t3600 -T -X >result.log, 400000')
        ##################
        
        
    ## 2
    if tcd.step("Start pythonsv and unlock all of sockets, pchs and uncores."):
        # Start pythonsv and unlock all of sockets, pchs and uncores.
        
        # Open C:\pythonsv\sapphirerapids, run below command
        
        tcd.itp.execute(f'unlock()')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Each Socket and PCH to be red unlock.")
        tcd.log("If pythonsv script get some error. Please do below command.")
        tcd.log(">>>unlock()")
        tcd.log(">>>itp.forcereconfig()")
        tcd.log(">>>sv.refresh()")
        ### Notes ###
        # Wiki of pythonsv:
        # https://wiki.ith.intel.com/pages/viewpage.action?pageId=1710639743
        ##################
        
        
    ## 3
    if tcd.step("Save pythonsv log and check UPI topolopy by below command in pythonsv:"):
        # Save pythonsv log and check UPI topolopy by below command in pythonsv:
        
        tcd.itp.execute(f'log(r"logpath")')
        tcd.itp.execute(f'import upi.upiStatus as us')
        tcd.itp.execute(f'us.printTopology()')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("The UPI Links output should be the same as UPI Topology. Any different, please Fail the test case.")
        tcd.log("For example, EGS 4_3_1 Topology:")
        tcd.log("4S6Q Topology")
        tcd.log("S0_P0 <------> S1_P1")
        tcd.log("S0_P1 <------> S3_P0")
        tcd.log("S0_P2 <------> S2_P2")
        tcd.log("S1_P0 <------> S2_P1")
        tcd.log("S1_P1 <------> S0_P0")
        tcd.log("S1_P2 <------> S3_P2")
        tcd.log("S2_P0 <------> S3_P1")
        tcd.log("S2_P1 <------> S1_P0")
        tcd.log("S2_P2 <------> S0_P2")
        tcd.log("S3_P0 <------> S0_P1")
        tcd.log("S3_P1 <------> S2_P0")
        tcd.log("S3_P2 <------> S1_P2")
        ##################
        
        
    ## 4
    if tcd.step("Check UPI link speed by below command in pythonsv:"):
        # Check UPI link speed by below command in pythonsv:
        
        tcd.itp.execute(f'us.printLinkSpeed()')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("For Birch Stream: Upi Link speed will be 24GT/s. Status will be Fast Mode. Tx State will be L0.")
        tcd.log("For Eagle Stream: Upi Link speed will be 16GT/s. Status will be Fast Mode. Tx State will be L0.")
        ##################
        
        
    ## 5
    if tcd.step("Check UPI B/W by below command in pythonsv:"):
        # Check UPI B/W by below command in pythonsv:
        
        tcd.itp.execute(f'sv.sockets.uncore.upi.upis.ktireut_ph_css.s_clm')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("For Birch Stream: Upi B/W will be 0x00000007")
        tcd.log("For Eagle Stream: Upi B/W will be 0x00000007")
        ##################
        
        
    ## 6
    if tcd.step("Check UPI Errors by below command in pythonsv:"):
        # Check UPI Errors by below command in pythonsv:
        
        tcd.itp.execute(f'us.printErrors()')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("The Value of below register must be 0x0, if not 0x0, please fail the test case.")
        tcd.log("kti_mc_ad")
        tcd.log("ktiph_rxl0c_err_sts")
        tcd.log("ktiph_rxloc_err_log0")
        tcd.log("ktiph_rxl0c_err_log1")
        tcd.log("ktiph_l0pexit_err")
        tcd.log("ktierrcnt0_cntr")
        tcd.log("ktierrcnt1_cntr")
        tcd.log("ktierrcnt2_cntr")
        tcd.log("kticrcerrcnt")
        tcd.log("ktiles")
        tcd.log("ktidbgerrst0")
        tcd.log("ktidbgerrst1")
        tcd.log("bios_kti_err_st")
        ### Notes ###
        # These value is base on EGS platform. Will update to BHS in the future.
        ##################
        
        
    ## 7
    if tcd.step("Just end the log og pythonsv:"):
        # Just end the log og pythonsv:
        
        tcd.itp.execute(f'nolog()')
        ##################
        
        
    ## 8
    if tcd.step("## Call TCDB test_tcdb Start"):
        
        ### Call TCDB test_tcdb Start
        for i in range(0, 20):
            # Test Tcd
        
            ## Set BIOS knob: VTdSupport=0x0
            set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x0")
            if set_cli:
                sut.xmlcli_os.set_bios_knobs("VTdSupport=0x0")
                sutos.reset_cycle_step(sut)
                tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x0"))
            
        
            ## Reset to OS
            tcd.reset()
            tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
            tcd.environment = "OS"
        
            sutos.execute_cmd(sut, f'python --help')
            sutos.execute_cmd(sut, f'python -c "print(1+1)", 20')
            tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        
            ## Reset to UEF SHELL
            sutos.execute_cmd(sut, f'{sutos.wr_cmd}', no_check=True)
            # Wait for: UEFI Shell
            sut.bios.enter_bios_setup()
            sut.bios.bios_setup_to_uefi_shell()
            Case.expect('in UEFI Shell', sut.bios.in_uefi())
            tcd.environment = "UEFI SHELL"
        ### Call TCDB test_tcdb End
        
        ##################
        
        
    ## 9
    if tcd.step("call following steps for test purpose"):
        # call following steps for test purpose
        UefiShell.execute_cmd(sut, f'ls')
        
        ## Reset to OS
        tcd.reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        tcd.environment = "OS"
        
        tcd.sleep(20)
        
        ## Reset to UEF SHELL
        sutos.execute_cmd(sut, f'{sutos.wr_cmd}', no_check=True)
        # Wait for: UEFI Shell
        sut.bios.enter_bios_setup()
        sut.bios.bios_setup_to_uefi_shell()
        Case.expect('in UEFI Shell', sut.bios.in_uefi())
        tcd.environment = "UEFI SHELL"
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
