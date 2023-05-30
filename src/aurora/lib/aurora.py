import csv
import json

from src.lib.toolkit.basic.log import logger
from src.lib.toolkit.basic.utility import get_xml_driver
from src.lib.toolkit.infra.bmc.bmc import RedfishController

# tool path setting
AURORA_TOOL_PATH = r'/opt/pv'
# AURORA_TOOL_PATH = r'/home/miaoxiao/tool'
# AURORA_TOOL_PATH = r'/home/BKCPkg/domains/PM'
SOCWATCH_PATH = f'{AURORA_TOOL_PATH}/socwatch'
PTU_PATH = f'{AURORA_TOOL_PATH}/ptu'
BURNIN_TEST_PATH = f'{AURORA_TOOL_PATH}/burnintest/64bit'
PMUTIL_BIN_PATH = f'{AURORA_TOOL_PATH}/pm_utility-master'
MLC_PATH = f'{AURORA_TOOL_PATH}/mlc/Linux'
DMIDECODE_PATH = f'{AURORA_TOOL_PATH}/dmidecode-master'
Stressapptest_PATH = f'{AURORA_TOOL_PATH}'
ILVSS_PATH = F'{AURORA_TOOL_PATH}/ilvss.0'

# config
SOCKET_NUM = 2
MEMORY_MC_NUM = 4
MEMORY_CH_NUM = 2
MEMORY_NUM_PER_SOCKET = 8
MEMORY_SIZE = 64   # unit is GB
MINIMUM_MEMORY_SIZE = 128  # unit is GB
# work around for Aurora, SNC can only be set by BMC, not bios
# https://wiki.ith.intel.com/pages/viewpage.action?pageId=2093633647
SNC_MODE_VALUE = ('snc2', 'snc4')
SNC_STRESSTESTAPP_PARAM = (720000, 620000)


def kill_process(sut, proc_name):
    _, stdout, _ = sut.execute_shell_cmd(f'ps aux | grep \'{proc_name}\' | grep -v grep', 30)
    if stdout != '':
        processes = str(stdout).splitlines()
        for process in processes:
            pid = process.split()[1]
            logger.debug(f'kill process: {process}')
            sut.execute_shell_cmd(f'kill -9 {pid}')


def ptu_mon_log_check(log_file, check_callback, skip_sec=10):
    with open(log_file, 'r') as fs:
        log_lines = fs.readlines()
        log_lines = [log_lines[index].split() for index in range(1, len(log_lines))]

        for log_line in log_lines:
            # No.0 column is Index for second data
            # skip previous 10 sec data
            if int(log_line[0]) < skip_sec:
                continue

            # No.2 column equal '-' means this line is summary of core
            if '-' in log_line[2]:
                # No.0 column is Index for second data, No.1 column is CPU
                # No.8 column is C0 data, No.9 column is C1 data, No.10 column is C6 data
                logger.debug(
                    f'will check Index {log_line[0]} Device {log_line[1]} C0 {log_line[8]} C1 {log_line[9]} C6 {log_line[10]}')
                check_callback(log_line[8], log_line[9], log_line[10])


def set_snc_via_redfish(sut, value):
    redfish_cfg = get_xml_driver('physical_control')
    redfish_cfg = redfish_cfg.find('./redfish')
    redfish_ctl = RedfishController(redfish_cfg.find('./ip').text, redfish_cfg.find('./username').text,
                                    redfish_cfg.find('./password').text)
    data = f'{{"SncEnabled": "{value}"}}'
    data = json.dumps(data)
    out = redfish_ctl.redfish_post('/redfish/v1/Systems/system/Bios', data)
    if not out:
        raise RuntimeError('set SNC failed')


class SocWatchLog:
    @classmethod
    def get_file_content(cls, log_file):
        with open(log_file, 'r') as fs:
            csv_iterator = csv.reader(fs)
            logs = list(csv_iterator)

        return logs

    @classmethod
    def get_pstate_cpu_idle(cls, log_file):
        logs_table = SocWatchLog.get_file_content(log_file)

        for log_row in logs_table:
            if len(log_row) > 0 and 'P-State' == log_row[0].strip():
                header_row = log_row
            if len(log_row) > 0 and 'CPU Idle' == log_row[0].strip():
                result_row = log_row

        ret = dict()
        for index in range(len(header_row)):
            if 'Residency' and '(%)' in header_row[index]:
                ret[header_row[index].strip()] = result_row[index].strip()

        return ret

    @classmethod
    def get_pstate_p0(cls, log_file):
        logs_table = SocWatchLog.get_file_content(log_file)

        result_rows = []
        for log_row in logs_table:
            if len(log_row) > 0 and 'P-State' == log_row[0].strip():
                header_row = log_row
            if len(log_row) > 0 and 'P0' == log_row[0].strip():
                result_rows.append(log_row)

        ret = dict()
        for index in range(len(header_row)):
            if 'Residency' and '(%)' in header_row[index]:
                ret[header_row[index].strip()] = []

                for result_row in result_rows:
                    ret[header_row[index].strip()].append(result_row[index].strip())

        return ret

    @classmethod
    def get_pstate_p1(cls, log_file):
        logs_table = SocWatchLog.get_file_content(log_file)

        for log_row in logs_table:
            if len(log_row) > 0 and 'P-State' == log_row[0].strip():
                header_row = log_row
            if len(log_row) > 0 and 'P1' == log_row[0].strip():
                result_row = log_row

        ret = dict()
        for index in range(len(header_row)):
            if 'Residency' and '(%)' in header_row[index]:
                ret[header_row[index].strip()] = result_row[index].strip()

        return ret

    @classmethod
    def get_cstate_cc6(cls, log_file):
        logs_table = SocWatchLog.get_file_content(log_file)

        for log_row in logs_table:
            if len(log_row) > 0 and 'C-State' == log_row[0].strip():
                header_row = log_row
            if len(log_row) > 0 and 'CC6' == log_row[0].strip():
                result_row = log_row

        ret = dict()
        for index in range(len(header_row)):
            if 'Residency' and '(%)' in header_row[index]:
                ret[header_row[index].strip()] = result_row[index].strip()

        return ret

    @classmethod
    def get_cstate_cc0(cls, log_file):
        logs_table = SocWatchLog.get_file_content(log_file)

        for log_row in logs_table:
            if len(log_row) > 0 and 'C-State' == log_row[0].strip():
                header_row = log_row
            if len(log_row) > 0 and 'CC0' == log_row[0].strip():
                result_row = log_row

        ret = dict()
        for index in range(len(header_row)):
            if 'Residency' and '(%)' in header_row[index]:
                ret[header_row[index].strip()] = result_row[index].strip()

        return ret

    @classmethod
    def get_cstate_cc1(cls, log_file):
        logs_table = SocWatchLog.get_file_content(log_file)

        for log_row in logs_table:
            if len(log_row) > 0 and 'C-State' == log_row[0].strip():
                header_row = log_row
            if len(log_row) > 0 and 'CC1' == log_row[0].strip():
                result_row = log_row

        ret = dict()
        for index in range(len(header_row)):
            if 'Residency' and '(%)' in header_row[index]:
                ret[header_row[index].strip()] = result_row[index].strip()

        return ret
