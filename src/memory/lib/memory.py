import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.os_scene import *
from tkconfig import sut_tool
from dtaf_core.lib.tklib.steps_lib.bios_knob import *


now_time = datetime.datetime.now().strftime('%Y%m%dZ%Hh%Mm%Ss')


def create_log_dir(sut):
    Case.step('create log folder')
    log_dir = ''
    if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
        SUT_TOOLS_LINUX_MEMORY = sut_tool('SUT_TOOLS_LINUX_MEMORY')
        log_dir = f'{SUT_TOOLS_LINUX_MEMORY}/log{now_time}'
        sut.execute_shell_cmd(rf'mkdir -p {log_dir}')
    elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
        SUT_TOOLS_WINDOWS_MEMORY = sut_tool('SUT_TOOLS_WINDOWS_MEMORY')
        log_dir = f'{SUT_TOOLS_WINDOWS_MEMORY}\\log{now_time}'
        sut.execute_shell_cmd(rf'mkdir {log_dir[0]}')
    return log_dir


def clear_system_log(sut):
    Case.step('clear system log')
    if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
        clear_dmesg_cmd = r'dmesg -C'
        sut.execute_shell_cmd(clear_dmesg_cmd)
        clear_message_log = r'echo "" > /var/log/messages'
        sut.execute_shell_cmd(clear_message_log)
    elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
        clear_syslog_cmd = r'clear-eventlog -log application, system'
        sut.execute_shell_cmd(clear_syslog_cmd, powershell=True)


def check_system_log(sut, log_dir):
    Case.step('check system log')
    assert log_dir, 'log_dir is empty'
    if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
        check_dmesg_cmd = rf"dmesg | tee {log_dir}/dmesg_log.txt"
        check_message_cmd = rf"cat /var/log/messages | tee {log_dir}/message_log.txt"
        stdout1 = sut.execute_shell_cmd(check_dmesg_cmd, cwd=log_dir)[1]
        stdout2 = sut.execute_shell_cmd(check_message_cmd, cwd=log_dir)[1]
        stdout = stdout1 + '\n' + stdout2
        key_word = ['Hardware Error']
        Case.expect('No Error or Fail log in system log', not any(i in stdout for i in key_word))
    elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
        # check_log_cmd = rf'Get-EventLog -LogName System | tee {log_dir}\event_log.txt'
        get_log_cmd = r'get-winevent system | where {($_.LevelDisplayName -match "Critical") -or ($_.LevelDisplayName -match "Error")}'
        check_log_cmd = rf"{get_log_cmd} | tee {log_dir}\event_log.txt"
        stdout = sut.execute_shell_cmd(check_log_cmd, powershell=True)[1]
        key_word = ['Error', 'Critical']
        Case.expect('No Error or Critical log in EventLog', not any(i in stdout for i in key_word))


def dimm_info_check(sut, cmd, compare_value, multiple=1):
    """
    :param sut: sut instance
    :param cmd: the command will be execute
    :param compare_value: the compare value stored in sut.ini, eg: socket, hw_dimm_number
    :param multiple: (optional) for specific case, node number = socket number * 2
    """
    get_value = sut.execute_shell_cmd(cmd)[1].strip()
    Case.expect(f'test pass', int(get_value) == int(sut.cfg['defaults'][compare_value]) * multiple)


def get_knob_info_in_cycle(key_word):
    """
    This method is used to get the line which contains the key word what you provide.
    Args:
        key_word: the string what you want to find in bios log
    Return:
        str. one line in bios log
    """
    bios_log_path = LOG_PATH + '\\bios.log'
    knob_line_list = find_lines(key_word, bios_log_path)
    return knob_line_list[-1]


def save_log_files(sut, log_dir):
    Case.step('save log files')
    assert log_dir, 'log_dir is empty'
    sut.download_to_local(remotepath=log_dir, localpath=os.path.join(LOG_PATH, 'result'))


def restore_env(sut, log_dir):
    Case.step('restore env')
    assert log_dir, 'log_dir is empty'
    restore_env_cmd = ''
    if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
        restore_env_cmd = f'rm -rf {log_dir}'
    elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
        restore_env_cmd = f'rd /s /q {log_dir}'
    sut.execute_shell_cmd(restore_env_cmd)


def stress_log_check(stress_log_name, key_word):
    stress_file_path = rf'{LOG_PATH}\result\log{now_time}\{stress_log_name}'
    with open(stress_file_path, 'r') as f:
        stress_result_text = f.read()
    Case.expect('run stress success', key_word in stress_result_text)
