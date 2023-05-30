import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.lib.toolkit.auto_api import *

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'it is a template for a general case which is executed by inband mode',
    'the case is expected to work for multiple os like Windows/Linux',
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # TODO: replace these with your own steps
    # Prepare steps - call predefined steps
    Case.prepare('case prepare description')
    # TODO: Check wether system is in OS.
    ret = sut.check_system_in_os()
    Case.expect('System is already in OS.', ret)

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
    impi_cmd = f"./{PM_IPMI_L}" + r" sensor list | grep -i 'dts cpu1' | awk '{print$4}'"
    ret, stdout, stderr = sut.execute_shell_cmd(cmd=impi_cmd)
    Case.expect('current temperature is lower than 50', int(stdout) < 50)

    # TODO: This step demonstrate how to download log file to LOG_PATH folder in HOST
    # Step 3 - call execute_shell_cmd to run command in sut
    Case.step('run command and save stdout in file')
    ret, stdout, stderr = sut.execute_shell_cmd('ping -c 5 192.168.0.2 > /home/result.txt')
    Case.expect('ping successful', ret == 0)

    # Step 4 - set and check bios knob via xmlcli tool
    Case.step('change bios knob via xmlcli tool')
    ret = sut.xmlcli_os.set_bios_knobs('ShellEntryTime=0x10')
    Case.expect('set bios knob successfully', ret)
    ret = sut.xmlcli_os.check_bios_knobs('ShellEntryTime=0x10')
    Case.expect('check bios knob successfully', ret)
    value = sut.xmlcli_os.get_bios_knobs_value('ShellEntryTime')
    Case.expect('get bios knob correctly', value['ShellEntryTime'] == 0x10)
    ret = sut.xmlcli_os.restore_default()
    Case.expect('restore all bios knobs to default value', ret)

    # TODO: remove all TODO notes before submitting code
    # TODO: reformat code (shortcut key is 'Ctrl + Alt + L') before submitting code


def clean_up(sut):
    # TODO: remove or restore files, kill sthreads and so on.
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
