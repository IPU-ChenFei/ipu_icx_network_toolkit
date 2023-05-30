import time

from auto_api import *
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from infra.xtp.itp import PythonsvSemiStructured
from src.lib.toolkit.steps_lib.domains.multisocket.multisocket import MultiSocket, Docker
from src.lib.toolkit.steps_lib.uefi_scene import UefiShell

CASE_DESC = [
    "Multisocket stress test using Stressapptest with mixed UPI link speed"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)

    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    # tar_name = ParameterParser.parse_parameter("tar_name") + "-latest"
    execution_time = int(ParameterParser.parse_parameter("execution_time"))
    stress_timeout = execution_time + 30

    Case.step('Unlock devices')
    itp.execute("unlock()")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("import random")

    Case.step("Setting random mixed link speed")
    # Todo set_mixed_api()

    Case.step("Reset to OS")
    UefiShell.reset_to_os(sut)

    Case.step("Check UPI link details")
    MultiSocket.check_upi_topology(itp)
    MultiSocket.check_upi_link_speed(itp, sut)
    MultiSocket.check_upi_s_clm(itp)
    MultiSocket.check_upi_print_error(itp)

    Case.step("Check NUMA node")
    sut.execute_shell_cmd("lscpu | grep 'node'")
    sut.execute_shell_cmd("dmesg -C")

    Case.step("Set up docker environment if needed")
    Docker.sut_docker_set_up(sut)

    Case.step("Reload docker environment for a successful docker execution")
    Docker.restart_docker_env(sut)

    Case.step("Grab Docker image from remote")
    Docker.download_docker_tar(sut, "stresstools-latest")

    Case.step("Run Stressapptest stress in Docker")
    sut.execute_shell_cmd(f"docker run -itd --name=stresstools-latest -p 2222:22 --privileged "
                          f"--net=docker-br0 --ip=172.100.0.2 stresstools:latest /sbin/init", timeout=60)
    time.sleep(20)

    sut.execute_shell_cmd("sshpass -p password ssh -p 22 root@172.100.0.2 "
                          "cd /stressapptest-master/stressapptest-master/src && "
                          f"./stressapptest -s {execution_time} "
                          "-M 25000 -C 100 -i 100 -m 100 -W --remote_numa -l stressapptest.log",
                          timeout=stress_timeout)

    Case.step("Check demsg in sut")
    _,  out, _ = sut.execute_shell_cmd("dmesg")
    logger.debug(out)

    Case.step("Check itp related")
    itp.execute("sv.refresh()")
    itp.execute("itp.forcereconfig()")
    MultiSocket.check_mce_error(itp)
    MultiSocket.check_mca_error(itp)

    Case.step("Remove container")
    sut.execute_shell_cmd("docker stop stresstools_latest")
    sut.execute_shell_cmd("docker rm stresstools-latest")

    Case.step("Reboot to UEFI and set bios back to default")
    my_os.reset_to_uefi_shell(sut)
    sut.restore_bios_defaults_xmlcli(SUT_STATUS.S0.UEFI_SHELL)

    Case.step("Cold reset")
    UefiShell.cold_reset_cycle_step(sut)

    itp.exit()


def clean_up(sut):
    Docker.restore_docker_file(sut)
    sut.execute_shell_cmd("docker stop stresstools-latest")
    sut.execute_shell_cmd("docker rm stresstools-latest")
    sut.restore_bios_defaults_xmlcli(SUT_STATUS.S0.UEFI_SHELL)


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

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
