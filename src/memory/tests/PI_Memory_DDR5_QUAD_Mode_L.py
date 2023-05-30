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
        if sut.socket_name == 'SPR':
             boot_to(sut, sut.default_os)
        # BIOS knob setting for QS CPU unlock
        if sut.socket_name == 'ICX':
            boot_to_with_bios_knobs(sut, sut.default_os, 'DciEn', '0x1', 'DelayedAuthenticationModeOverride', '0x1',
                                    'DelayedAuthenticationMode', '0x1')
            sutos.g3_cycle_step(sut)



    # Tool Version [0.2.2]
    #ID: 15010602068
    #TITLE: PI_Memory_DDR5_QUAD_Mode_L
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
        # Platform cooling fans running with 100% rpm to avoid CPU performance related issues due to thermal events
        # Prepare Steps
        # Git Pull Pythonsv-Sapphirerapids project and Update tools (startspr.py)
        tcd.itplib = "pythonsv"
        # SUT booting into Linux with supported POR memory config:1DPC Or 2DPC
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # Enable Quad
        # Mode option Boot to BIOS configure
        ## Set BIOS knob: SncEn=0x0, UmaBasedClustering=0x4
        set_cli = not sut.xmlcli_os.check_bios_knobs("SncEn=0x0, UmaBasedClustering=0x4")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("SncEn=0x0, UmaBasedClustering=0x4")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("SncEn=0x0, UmaBasedClustering=0x4"))
        
        
        
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
        if tcd.step("Boot to OS and verify Quad mode is enabled"):
            # Boot to OS and verify Quad mode is enabled
            # PythonSV:
            tcd.itp.execute(f'itp.unlock()')
            time.sleep(10)
            if sut.socket_name == 'ICX':
                tcd.itp.execute(f'print(sv.sockets.uncore.ms2idi0.snc_config)')
            if sut.socket_name == 'SPR':
                tcd.itp.execute(f'print(sv.sockets.uncore.cha.cha0.ms2idi0.snc_config)')

            Case.step('check itp get result')
            itp_get_file = rf'{LOG_PATH}\last_itp_cmd_out.txt'
            with open(itp_get_file, 'r') as f:
                itp_get_result = f.read()
            Case.expect('return value is 0xe, Quad mode is enabled', '0x0000000e' in itp_get_result)

            # tcd.itp.execute(f'sv.sockets.uncore.cha.cha0.ms2idi0.snc_config')
            ##################
            tcd.log("### Expected result ###")
            tcd.log("Result should be 0xe for all of sockets")
            ### Notes ###
            # Step
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
                    rf"./mlc --peak_injection_bandwidth -Z -t{runtime} > {log_dir}/Mlc_Test_Result.txt",
                    cwd="/root/mlc/Linux")
                Case.sleep(runtime * 5 + 60)
                ##################
                tcd.log("### Expected result ###")
                tcd.log("1) Test passed")
                tcd.log("2) No hang or no reboot")
                ### Notes ###
                # Step 5
                ##################

        ## 4
            Case.step("check system event log :")
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
