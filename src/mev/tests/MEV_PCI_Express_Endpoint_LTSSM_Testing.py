from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp
from src.mev.lib.utility import get_bdf
from src.configuration.config.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV

CASE_DESC = [
    # TODO
    'PCI Express - Endpoint LTSSM Testing',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        # Prepare steps - call predefined steps
        boot_to(sut, sut.default_os)

        # Step1 - check MEV device on SUT
        Case.step('get pci device info')
        _, stdout, _ = sut.execute_shell_cmd('lspci | egrep "1452|1453"', 30)
        Case.expect('check mev device info for 1452', '1452' in stdout)

        bdf = get_bdf(sut.execute_shell_cmd, 1452, 0)
        bus = bdf.split(":")[1]

        return_code, _, _ = sut.execute_shell_cmd("ipmitool sel clear", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('return value is 0', return_code == 0)

        # Step2 - check MEV card width and speed
        Case.step('get pci device width and speed')
        _, stdout, _ = sut.execute_shell_cmd(f"lspci -s {bdf} -vv | grep -i lnk", 30)
        Case.expect('check pci device width and speed',
                    'Speed 16GT/s' in stdout and 'Width x16' in stdout)
        Case.step('Get BUS id')

        # Step3 - To disable drivers in Linux
        Case.step('To disable drivers in Linux')
        return_code, stdout, stderr = sut.execute_shell_cmd(f'lspci -s {bdf} -vv', 30)
        # Case.expect('return value not keyword Kernel driver in use: idpf',
        #             find_keyword('Kernel driver in use: idpf', stdout))
        if 'Kernel driver in use: idpf' in stdout:
            return_code, _, _ = sut.execute_shell_cmd('modprobe -r idpf', 30)
            Case.expect('return value is 0', return_code == 0)
            _, stdout, _ = sut.execute_shell_cmd(f'lspci -s {bdf} -vv', 30)
            Case.expect('return value not keyword Kernel driver in use: idpf',
                        'Kernel driver in use: idpf' not in stdout)

        # Step4 - Run the PML1 (D3hot) test for 1000 cycles
        Case.step('Run the PML1 (D3hot) test for 1000 cycles')
        _, stdout, _ = sut.execute_shell_cmd(
            f"./LTSSMtool pml1 1000 [0x{bus},16,4] -l /home", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # Step5 - Run the Recovery test for 100 cycles
        Case.step('Run the Recovery test for 100 cycles')
        _, stdout, _ = sut.execute_shell_cmd(
            f"./LTSSMtool linkRetrain 100 [0x{bus},16,4] -l /home", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # Step6 - Run the Link Disable test for 100 cycles
        Case.step('Run the Link Disable test for 100 cycles')
        _, stdout, _ = sut.execute_shell_cmd(
            f"./LTSSMtool linkDisable 100 [0x{bus},16,4] -l /home", 80, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # Step7 - Run the SpeedChange test for 100 cycles
        Case.step('Run the SpeedChange test for 100 cycles')
        _, stdout, _ = sut.execute_shell_cmd(
            f"./LTSSMtool speedChange 100 [0x{bus},16,4] -all -l /home", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # # Step8 - Run the Function Level Reset (FLR) test for 100 cycles
        Case.step('Run the Function Level Reset (FLR) test for 100 cycles')
        _, stdout, _ = sut.execute_shell_cmd(f"./LTSSMtool flr 100 [0x{bus},16,4] -l /home", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # Step9 - Run the Tx Equalizer Retrain test for 100  cycles
        Case.step('Run the Tx Equalizer Retrain test for 100 cycles')
        _, stdout, _ = sut.execute_shell_cmd(
            f"./LTSSMtool txEqRedo 100 [0x{bus},16,4] -l /home", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # Step10 - Run the Secondary Bus Reset (SBR) test for 1000 cycles
        Case.step('Run the Secondary Bus Reset (SBR) test for 1000 cycles')
        _, stdout, _ = sut.execute_shell_cmd(f"./LTSSMtool sbr 100 [0x{bus},16,4] -l /home", 60, cwd=SUT_TOOLS_LINUX_MEV)
        Case.expect('check Error Summary value is [PASSED]', 'PASSED' in stdout)

        # Step11 - Check the SEL for PCIe errors related to the device under test
        Case.step('Check the SEL for PCIe errors related to the device under test')
        _, stdout, _ = sut.execute_shell_cmd("ipmitool sel list | grep -i 'pcie error'", 60)
        Case.expect('Check for no PCIe errors in the SEL ', 'error' not in stdout)
    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


def clean_up(sut):
    pass


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <json file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
