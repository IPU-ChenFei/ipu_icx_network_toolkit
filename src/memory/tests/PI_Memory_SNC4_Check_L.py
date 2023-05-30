# Tool Version [0.2.2]
CASE_DESC = [
    "it is a python script generated from validation language"
]
from dtaf_core.lib.tklib.basic.testcase import Result
from dtaf_core.lib.tklib.steps_lib.vl.vltcd import *
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell, BIOS_Menu
from dtaf_core.lib.tklib.steps_lib.os_scene import GenericOS
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from plat_feature_config import *
from src.memory.lib.memory import *


def test_steps(tcd):
    sut = tcd.sut
    sutos = tcd.sut.sutos
    assert (issubclass(sutos, GenericOS))
    tools = get_tool(tcd.sut)

    if tcd.prepare("boot to OS"):
        boot_to(sut, sut.default_os)


    # Tool Version [0.2.2]
    #ID: 15010580956
    #TITLE: PI_Memory_SNC4_Check_L
    #DOMAIN: memory
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Hardware and Infrastructure Setup
        # Ensure Linux OS present in the platform (Ingredient: Latest BKC OS images) and Configure it first in boot order
        # Platform should flashed with latest BKC#N ingredients like IFWI, BMC, CPLD
        # BMC is in interactive mode
        # Git Pull Pythonsv-Sapphirerapids project and Update tools
        # Platform should have POR memory config: 1DPC/2DPC
        # Ensure covering DDR5 vendors: Hynix, Micron, Samsung
        # Platform cooling fans running with 100% rpm to avoid CPU performance related issues due to thermal eventsHardware and Infrastructure Setup Prepare Steps
        # SUT booting into Linux with supported POR memory config:1DPC Or 2DPC
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # Enable SNC :
        ## Set BIOS knob: SncEn=0x4
        set_cli = not sut.xmlcli_os.check_bios_knobs("SncEn=0x4")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("SncEn=0x4")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("SncEn=0x4"))
        
        
        
    #################################################################
    # Steps Section
    #################################################################

    ## 0
    clear_system_log(sut)
    log_dir = create_log_dir(sut)

    try:

        ## 1
        if tcd.step("In OS, Check the dimm number :"):
            # In OS, Check the dimm number :
            sutos.execute_cmd(sut, f'dmidecode -t 17 | grep -E -v "No|Vo" | grep "Size" | nl')
            dimm_check_cmd = f'./dimm_info_check.sh | tee {log_dir}/dimm_info_check.txt | grep PASS'
            ret_code, stdout, stderr = sut.execute_shell_cmd(dimm_check_cmd, cwd="/root/sut_scripts")
            Case.expect('dimm info check pass', ret_code == 0)
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
            node_info_cmd = f'ls -d /sys/devices/system/node/node* | wc -l'
            dimm_info_check(sut, node_info_cmd, 'socket', 4)
            ##################
            tcd.log("### Expected result ###")
            tcd.log("Make sure that the numbers of nodes are as expected")
            tcd.log("SNC2 shoule be:number of sockets")
            ### Notes ###
            # Step 4
            ##################

        ## 3
        if tcd.step("Run MLC for 12 hours: ./mlc --peak_injection_bandwidth -Z -t43200"):
            # sutos.execute_cmd(sut, f'{tools.mlc_l.ipath}/Linux/mlc --peak_injection_bandwidth -Z -t20',
            #                   timeout=80 * 60)
            runtime = ParameterParser.parse_parameter("runtime")
            if runtime == '':
                runtime = 20
            else:
                runtime = int(runtime)
            sut.execute_shell_cmd_async(
                rf"./mlc --peak_injection_bandwidth -Z -t{runtime} > {log_dir}/Mlc_Test_Result.txt", cwd="/root/mlc/Linux")
            Case.sleep(runtime * 5 + 60)
            ##################
            tcd.log("### Expected result ###")
            tcd.log("1) Test passed")
            tcd.log("2) No hang or no reboot")
            ### Notes ###
            # Step 5
            ##################

            ## 4
            Case.step("check system event log:")
            check_system_log(sut, log_dir)
    finally:
        save_log_files(sut, log_dir)
        restore_env(sut, log_dir)
        restore_bios_defaults_xmlcli_step(sut, SUT_STATUS.S0.LINUX)
        stress_log_check('Mlc_Test_Result.txt', 'Stream-triad like')



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
