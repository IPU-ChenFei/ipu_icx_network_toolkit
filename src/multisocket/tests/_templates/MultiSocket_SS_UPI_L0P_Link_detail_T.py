# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell

from src.multisocket.lib.multisocket import MultiSocket

CASE_DESC = [
    'Check UPI Link Topology, LinkSpeed, B/W and UPI link Error via ITP by pythonsv in UPI L0p mode'
]


def check_upi_l0p_state(output):
    for line in output.splitlines():
        register_value = line.split('-')[1]
        register_value = int(register_value.strip(), 16)
        Case.expect('register value > 0', register_value > 0)


def test_steps(sut, my_os, globals_vars, local_vars):
    # type: (SUT, GenericOS) -> None
    Case.prepare('boot to UEFI & launch itp')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    itp = PythonsvSemiStructured(sut.socket_name, globals_vars, local_vars)
    itp.execute('unlock()')

    Case.step("set UPI link state of L0p to enable")
    knob_setting = "=".join(bios_knob('upi_link_l0p_enable_xmlci'))
    itp.execute('import pysvtools.xmlcli.XmlCli as cli')
    itp.execute('cli.clb._setCliAccess("itpii")')
    itp.execute(f'cli.CvProgKnobs("{knob_setting}")')

    Case.step("Cold reset to os")
    UefiShell.reset_to_os(sut)

    Case.step("Set the default EPB profile 0 to allow L0p")
    itp.execute("sv.sockets.uncore.upi.upis.ktil0pctrl0_l0.l0p_enable=1")

    Case.step("Check UPI L0p state by read register ktictrrxl0p and ktictrtxl0p")
    output = itp.execute("print(sv.sockets.uncore.upi.upis.ktictrrxl0p)")
    check_upi_l0p_state(output)
    output = itp.execute("print(sv.sockets.uncore.upi.upis.ktictrtxl0p)")
    check_upi_l0p_state(output)

    Case.step("Check upi link details")
    MultiSocket.check_upi_topology(itp)
    MultiSocket.check_upi_link_speed(itp, sut)
    MultiSocket.check_upi_s_clm(itp)
    MultiSocket.check_upi_print_error(itp)

    Case.step("Reboot to UEFI shell")
    my_os.reset_to_uefi_shell(sut)

    Case.step("restore bios knobs to default")
    itp.execute('cli.CvLoadDefaults()')

    Case.step("Reboot to OS")
    UefiShell.reset_to_os(sut)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    if Result.returncode != 0:
        cleanup.clear_cmos(sut)
        cleanup.to_s5(sut)


def test_main(globals_vars, local_vars):
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
        test_steps(sut, my_os, globals_vars, local_vars)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main(globals(), locals())
    exit(Result.returncode)

