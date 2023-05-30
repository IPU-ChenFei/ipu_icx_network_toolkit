import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.lib.toolkit.auto_api import *
from src.lib.toolkit.basic.config import LOG_PATH
from src.lib.toolkit.basic.utility import ParameterParser
from src.lib.toolkit.steps_lib import cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to_with_bios_knobs

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'it is a template for a general case',
    'the case is expected to work for multiple os like Windows/Linux/VMWare',
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # TODO: replace these with your own steps
    # Prepare steps - call predefined steps
    Case.prepare('case prepare description')
    # TODO: Define bios knobs variable in wht_bios.py(for whitely platform), please reference guideline in wht_bios.py
    #   Call "bios_knob from src.lib.toolkit.steps_lib.config" function, and pass bios knobs variable as a string to param just like example
    #   Variable name must end with '_xmlcli'(for XMLCLI) or '_serial'(for BIOS serial)
    #   Don't hard code bios knob variable in case content
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_security_common_xmlcli'))
    # equal
    # boot_to(sut, sut.default_os)
    # set_bios_knobs_step(sut, *bios_knob('knob_setting_security_common_xmlcli'))

    # TODO: This step is a standard case step template
    # Step 1 - call execute_shell_cmd to run command in sut
    # call Case.step before each step
    Case.step('case step description, you can copy from TCD')
    ret, stdout, stderr = sut.execute_shell_cmd('ping -c 5 192.168.0.2')
    # call Case.expect to check step execution is successful, especially for command return code
    Case.expect('ping successful', ret == 0)
    # check keywords of stdout when check ret value can not judge command execution is successful
    # ping 5 times without packet loss means ping command execution is really successful
    loss_data = re.search(r'(\d+)% packet loss', stdout).group(1)
    Case.expect('ping successful', int(loss_data) == 0)

    # TODO: This step demonstrate how to reference third party tool
    #   Third party tool path must be defined in sut_tool.py, please reference guideline in sut_tool.py
    #   Don't hard code absolute path in case content
    # Step 2 - call execute_shell_cmd to run command in sut
    Case.step('use third party tool to get cpu temperature')
    impi_cmd = f"./{sut_tool('PM_IPMI_L')}" + r" sensor list | grep -i 'dts cpu1' | awk '{print$4}'"
    ret, stdout, stderr = sut.execute_shell_cmd(cmd=impi_cmd)
    Case.expect('current temperature is lower than 50', int(stdout) < 50)

    # TODO: This step demonstrate how to download log file to LOG_PATH folder in HOST
    # Step 3 - call execute_shell_cmd to run command in sut
    Case.step('run command and save stdout in file')
    ret, stdout, stderr = sut.execute_shell_cmd('ping -c 5 192.168.0.2 > /home/result.txt')
    Case.expect('ping successful', ret == 0)
    # TODO: All log files downloaded from SUT must be saved in LOG_PATH folder
    sut.download_to_local(remotepath='/home/result.txt', localpath=LOG_PATH)

    # Step 4 - call predefined steps
    my_os.warm_reset_cycle_step(sut)

    # TODO: remove all TODO notes before submitting code

    # TODO: reformat code (shortcut key is 'Ctrl + Alt + L') before submitting code


def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # set_bios_knobs_step(sut, *bios_knob('disable_wol_s5_xmlcli'))

    # TODO: by default, use cleanup.default_cleanup() for all scripts, for special purpose, call other function in cleanup module
    cleanup.default_cleanup(sut)


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
