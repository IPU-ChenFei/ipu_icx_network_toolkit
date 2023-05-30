# Tool Version [0.2.1]
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

    # Tool Version [0.2.1]
    # ID: 15010581424
    # TITLE: PI_Memeory_DDR5_Hemi_Mode_Stressapp_L
    # DOMAIN: memory

    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Hardware and Infrastructure Setup BMC is in interactive mode
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

        # Enable Hemi Mode option Boot to BIOS configure
        ## Set BIOS knob: SncEn=0x0, UmaBasedClustering=0x2
        set_cli = not sut.xmlcli_os.check_bios_knobs("SncEn=0x0, UmaBasedClustering=0x2")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("SncEn=0x0, UmaBasedClustering=0x2")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("SncEn=0x0, UmaBasedClustering=0x2"))

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
        if tcd.step("Boot to OS and verify Hemi mode is enabled"):
            # Boot to OS and verify Hemi mode is enabled
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
            Case.expect('return value is 0x6, Hemi mode is enabled', '0x00000006' in itp_get_result)

            # tcd.itp.execute(f'sv.sockets.uncore.cha.cha0.ms2idi0.snc_config')
            ##################
            tcd.log("### Expected result ###")
            tcd.log("Result should be 0x6 for all of sockets")
            ### Notes ###
            # Step 2
            ##################

        ## 3
        if tcd.step("pls install latest version of stressapptest-master, stress, and run below memory stress :"):
            # pls install latest version of stressapptest-master, stress, and run below memory stress :

            # sutos.execute_cmd(sut, f'{tools.stressapp_l.ipath}/src/stressapptest -s 600 -M -m -W', timeout=12 * 60)
            runtime = ParameterParser.parse_parameter("runtime")
            if runtime == '':
                runtime = 120
            else:
                runtime = int(runtime)
            sut.execute_shell_cmd_async(
                    rf"./stressapptest -s {runtime} -M -m -W > {log_dir}/stressapp_Test_Result.txt", cwd="/root")
            Case.sleep(runtime + 60)

            ##################
            tcd.log("### Expected result ###")
            tcd.log("1)No hang or reboot")
            tcd.log("2)Test passed")
            ### Notes ###

        ## 4
            Case.step("check system event log :")
            check_system_log(sut, log_dir)

    finally:
        save_log_files(sut, log_dir)
        restore_env(sut, log_dir)
        restore_bios_defaults_xmlcli_step(sut, SUT_STATUS.S0.LINUX)
        stress_log_check('stressapp_Test_Result.txt', 'Status: PASS')


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
