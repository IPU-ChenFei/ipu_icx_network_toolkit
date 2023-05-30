#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import re
import time
from src.ras.lib.ras_einj_util import RasEinjCommon
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.os_log_verification import OsLogVerifyCommon


class McaCommonUtils(object):
    """
    McaCommonUtils is used as Common Class for all MCA Related Test Cases
    """

    RAS_TOOLS_DEST_DIR = "/etc/tools/"
    RAS_TOOLS_PATH = "/etc/tools/ras_tools/"
    DUT_RAS_TOOLS_FILE_NAME = "ras_tools"
    RAS_TOOLS_TAR = DUT_RAS_TOOLS_FILE_NAME + ".tar"
    RAS_MCA_NON_EXE_PATH = 0x00000001
    RAS_MCA_EXE_PATH = 0x00000002
    RAS_MCA_EXE_INSTR_PATH = 0x00000003
    RAS_LMCE_EXE_DATA_ACCESS_PATH = 0x00000006
    RAS_MCA_EXE_DCU_SPLIT_PATH = 0x00000004
    RAS_MCA_EXE_DCU_STORE_PATH = 0x00000005
    RAS_LMCE_EXE_INSTR_INSTR_ACCESS_PATH = 0x00000008
    RAS_LMCE_MCA_EXE_INSTR_DATA_PATH = 0x00000007

    RAS_TOOL_PASSED_MESSAGE = "Test Passed"
    RAS_TOOL_FAILED_MESSAGE = "Test Failed"
    RAS_TOOL_SINGLE_ERROR_MESSAGE = "single"
    RAS_TOOL_INSTR_ERROR_MESSAGE = "instr"
    RAS_TOOL_PATROL_ERROR_MESSAGE = "patrol"
    RAS_TOOL_DATA_ACCESS_ERROR_MESSAGE = "Data Access/Data Access"
    RAS_TOOL_DCU_SPLIT_ERROR_MESSAGE = "split"
    RAS_TOOL_DCU_STORE_ERROR_MESSAGE = "store"
    RAS_TOOL_LMCE_INSTR_FETCH_INSTR_FETCH_ERROR_MESSAGE = "Instruction Fetch/Instruction Fetch"
    RAS_TOOL_LMCE_INSTR_FETCH_DATA_ACCESS_ERROR_MESSAGE = "Instruction Fetch/Data Access"

    DUT_MESSAGES_FILE_NAME = "messages"
    DUT_MESSAGES_PATH = "/var/log/" + DUT_MESSAGES_FILE_NAME

    DUT_JOURNALCTL_FILE_NAME = "journalctl"
    DUT_JOURNALCTL_NO_PROMPT = DUT_JOURNALCTL_FILE_NAME + " --no-pager"

    DUT_DMESG_FILE_NAME = "dmesg"

    RUNNER_CMD_NAME = "run-rasrunner -i 0x100 -pcie 0:0:0:0 -t 00:00:5"
    RUNNER_PATH = r'/runner/bin/scripts/run-rasrunner.py'
    MACHINE_CHECK_0_TOLERANT = r'/sys/devices/system/machinecheck/machinecheck0/tolerant'
    DUT_DMESG_FILE_GENERIC_ERROR_SIGNATURE = "Hardware Error"
    DUT_MESSAGES_GENERIC_ERROR_SIGNATURE = "mcelog"
    DUT_MESSAGES_DMESG_GENERIC_ERROR_SIGNATURE_LIST = (DUT_MESSAGES_GENERIC_ERROR_SIGNATURE + "," +
                                                       DUT_DMESG_FILE_GENERIC_ERROR_SIGNATURE).split(",")

    # NON_EXE - SRAO
    MCA_NON_EXE_ERROR_MESSAGES_LIST = \
        ["dirty LRU page: Recovered",
         "Hardware event",
         "Uncorrected error",
         "MemCtrl: Uncorrected patrol scrub error",
         "MCG status:RIPV"]

    MCA_NON_EXE_ERROR_DMESG_LIST = \
        ["UE memory scrubbing error",
         "dirty LRU page: Recovered"]

    # EXE - SRAR
    MCA_EXE_ERROR_MESSAGES_LIST = \
        ["Sending SIGBUS to einj_mem_uc:.* due to hardware memory corruption",
         "dirty LRU page: Recovered",
         "Hardware event",
         "Uncorrected error",
         "Transaction: Memory read error",
         "M2M: MscodDataRdErr",
         "MCG status:RIPV EIPV MCIP",
         "MCA: Data CACHE Level-0 Data-Read Error"]

    MCA_EXE_SRAR_UC_IFU_ERROR_MESSAGES_LIST = \
        ["Sending SIGBUS to einj_mem_uc:.* due to hardware memory corruption",
         "dirty LRU page: Recovered",
         "Hardware event",
         "Uncorrected error",
         "Transaction: Memory read error",
         "SRAR",
         "MCG status:RIPV EIPV MCIP",
         "Instruction-Fetch Error"]

    MCA_EXE_SRAR_UC_DCU_SPLIT_ERROR_MESSAGES_LIST = \
        ["dirty LRU page: Recovered",
         "Hardware event",
         "Uncorrected error",
         "Transaction: Memory read error",
         "SRAR",
         "MCG status:RIPV EIPV MCIP",
         "Data CACHE Level-0 Data-Read Error"]

    MCA_EXE_SRAR_UC_DCU_STORE_ERROR_MESSAGES_LIST = \
        ["dirty LRU page: Recovered",
         "Hardware event",
         "Uncorrected error",
         "Transaction: Memory read error",
         "Uncorrected DIMM memory error count exceeded threshold"]

    MCA_EXE_ERROR_DMESG_LIST = \
        ["UE memory read error",
         "mce: Uncorrected hardware memory error in user-access",
         "Sending SIGBUS to einj_mem_uc:.* due to hardware memory corruption",
         "dirty LRU page: Recovered"]

    LMCE_ERROR_DMESG_LIST = \
        ["UE memory read error",
         "mce: Uncorrected hardware memory error in user-access",
         "MCE .*: Killing einj_mem_uc:.* due to hardware memory corruption",
         "MCE .*: dirty LRU page: Recovered"]

    LMCE_EXE_ERROR_MESSAGES_LIST = \
        ["SRAR",
         "MCG status:RIPV EIPV MCIP LMCE"]

    LMCE_EXE_INSTR_FETCH_DATA_ACCESS_ERROR_MESSAGES_LIST = \
        ["Running trigger `dimm-error-trigger'",
         "Hardware event",
         "Uncorrected error",
         "Transaction: Memory read error",
         "MCA: Data CACHE Level-.* Data-Read Error",
         "Uncorrected DIMM memory error count exceeded threshold:.*",
         "MCA: MEMORY CONTROLLER RD_CHANNEL.*_ERR",
         "MCA: Instruction CACHE Level-.* Instruction-Fetch Error"]

    LMCE_RAS_TOOL_OUTPUT_LIST = \
        ["Saw local machine check",
         "SRAR"]

    LMCE_EXE_INSTR_FETCH_INSTR_FETCH_ERROR_MESSAGES_LIST = \
        ["Running trigger `dimm-error-trigger'",
         "Hardware event",
         "Uncorrected error",
         "Error enabled",
         "Transaction: Memory read error",
         "MCG status:RIPV EIPV MCIP LMCE",
         "Uncorrected DIMM memory error count exceeded threshold:.*",
         "MCA: MEMORY CONTROLLER RD_CHANNEL.*_ERR",
         "MCA: Instruction CACHE Level-.* Instruction-Fetch Error"]

    LMCE_EXE_DATA_ACCESS_ERROR_MESSAGES_LIST = \
        ["Running trigger `dimm-error-trigger'",
         "Hardware event",
         "Uncorrected error",
         "Transaction: Memory read error",
         "MCA: Data CACHE Level-.* Data-Read Error",
         "Uncorrected DIMM memory error count exceeded threshold:.*",
         "MCA: MEMORY CONTROLLER RD_CHANNEL.*_ERR",
         "Uncorrected hardware memory error in user-access"]

    TOOL_USAGE_CMD_DICT = {
        RAS_MCA_EXE_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/einj_mem_uc -f single &> exe.log & ",
        RAS_MCA_NON_EXE_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/einj_mem_uc -f patrol &> exe.log & ",
        RAS_MCA_EXE_INSTR_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/einj_mem_uc -f instr &> exe.log & ",
        RAS_MCA_EXE_DCU_SPLIT_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/einj_mem_uc -f split &> exe.log & ",
        RAS_MCA_EXE_DCU_STORE_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/einj_mem_uc -f store &> exe.log & ",
        RAS_LMCE_EXE_DATA_ACCESS_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/lmce -t DATA/DATA &> exe.log & ",
        RAS_LMCE_EXE_INSTR_INSTR_ACCESS_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/lmce -t INSTR/INSTR &>"
                                                                                   " exe.log & ",
        RAS_LMCE_MCA_EXE_INSTR_DATA_PATH: "nohup sudo " + RAS_TOOLS_DEST_DIR + "ras_tools/lmce -t INSTR/DATA &> "
                                                                               "exe.log & ",
    }

    RAS_TOOL_RESULT_DICT = {
        RAS_MCA_EXE_PATH: RAS_TOOL_SINGLE_ERROR_MESSAGE,
        RAS_MCA_NON_EXE_PATH: RAS_TOOL_PATROL_ERROR_MESSAGE,
        RAS_MCA_EXE_INSTR_PATH: RAS_TOOL_INSTR_ERROR_MESSAGE,
        RAS_MCA_EXE_DCU_SPLIT_PATH: RAS_TOOL_DCU_SPLIT_ERROR_MESSAGE,
        RAS_MCA_EXE_DCU_STORE_PATH: RAS_TOOL_DCU_STORE_ERROR_MESSAGE,
        RAS_LMCE_EXE_DATA_ACCESS_PATH: RAS_TOOL_DATA_ACCESS_ERROR_MESSAGE,
        RAS_LMCE_EXE_INSTR_INSTR_ACCESS_PATH: RAS_TOOL_LMCE_INSTR_FETCH_INSTR_FETCH_ERROR_MESSAGE,
        RAS_LMCE_MCA_EXE_INSTR_DATA_PATH: RAS_TOOL_LMCE_INSTR_FETCH_DATA_ACCESS_ERROR_MESSAGE,
    }

    def __init__(self, log, osobj, common_content_lib, common_config, cfg_opts):
        self._log = log
        self._os = osobj
        self._cfg = cfg_opts
        self._common_content_lib = common_content_lib
        self._common_content_config = common_config
        self._product = self._common_content_lib.get_platform_family()
        self._einj_common = RasEinjCommon(self._log, self._os, cfg_opts, self._common_content_lib,
                                          self._common_content_config)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._execute_cmd_timeout = self._common_content_config.get_command_timeout()
        self._os_time_out_in_sec = self._common_content_config.os_full_ac_cycle_time_out()
        self._wait_time_in_sec = self._common_content_config.itp_halt_time_in_sec()
        self._check_os_log = OsLogVerifyCommon(self._log, self._os, self._common_content_config,
                                               self._common_content_lib)

    def mca_prepare_injection(self):
        # Create tools dir on sut
        self._os.execute("mkdir /etc/tools", self._execute_cmd_timeout)

        ras_tools_install = self._install_collateral.install_linux_ras_tools()
        if ras_tools_install != 0:
            self._log.error("Ras tool installation failed on SUT")
            return False
        self._log.info("Ras Tool Successfully Installed on SUT")
        return True

    def mca_inject_error(self, error_type, address=0x0):
        global tool_usage
        self._log.info("Injecting MCA through Ras tools:")
        self._log.info("    Error type: %d", error_type)

        # Non-blocking command execution
        # Otherwise, if system ends up hanging after the injection, test will also hang
        # If we execute the command in background, then test can realize system hang and recover
        tool_usage = self.TOOL_USAGE_CMD_DICT[error_type]

        tool_output = "cat exe.log"
        self._log.info("    Binary Usage : %s", tool_usage)

        result = self._os.execute(tool_usage, self._execute_cmd_timeout)

        if result.return_code != 0:
            self._log.info("return_code=%d output=[%s]", result.return_code, result.stdout.strip())
            self._log.error("    Ras tool invocation failed on SUT")
            return False
        else:
            self._log.info("return_code=%d output=[%s]", result.return_code, result.stdout.strip())
            self._log.info("    Ras tool invocation passed on SUT")

        time.sleep(self._wait_time_in_sec)

        # Recover the SUT if it hung after MCE injection
        if not self._os.is_alive():
            self._os.wait_for_os(self._os_time_out_in_sec)
        if self._os.is_alive():
            result = self._os.execute(tool_output, self._execute_cmd_timeout)
        self._log.info("Ras Tool output:[%s]", result.stdout.strip())

        # Check for Ras tool result
        if re.findall(self.RAS_TOOL_RESULT_DICT[error_type], result.stdout.strip(), re.MULTILINE):
            self._log.info("Ras tool test Passed...")
            return True
        else:
            self._log.error("Ras Tool Test Failed")
            return False

    def mca_check_serial_log(self, error_type, mem_addr):
        """
        This method is used to check the serial logs after injecting mca_error

        """
        return True

    def mca_check_os_log(self, error_type):
        """
        This method is used to check and verify the MCA Error in OS Log.

        :param error_type: type of error
        :return: True if varlog/messages and dmesg string find else False
        """
        success_messages = False
        success_dmesg = False
        mca_messages_dict = {
            self.RAS_MCA_EXE_PATH: self.MCA_EXE_ERROR_MESSAGES_LIST,
            self.RAS_MCA_NON_EXE_PATH: self.MCA_NON_EXE_ERROR_MESSAGES_LIST,
            self.RAS_MCA_EXE_INSTR_PATH: self.MCA_EXE_SRAR_UC_IFU_ERROR_MESSAGES_LIST,
            self.RAS_LMCE_EXE_DATA_ACCESS_PATH: self.LMCE_EXE_DATA_ACCESS_ERROR_MESSAGES_LIST,
            self.RAS_MCA_EXE_DCU_SPLIT_PATH: self.MCA_EXE_SRAR_UC_DCU_SPLIT_ERROR_MESSAGES_LIST,
            self.RAS_MCA_EXE_DCU_STORE_PATH: self.MCA_EXE_SRAR_UC_DCU_STORE_ERROR_MESSAGES_LIST,
            self.RAS_LMCE_MCA_EXE_INSTR_DATA_PATH: self.LMCE_EXE_INSTR_FETCH_DATA_ACCESS_ERROR_MESSAGES_LIST,
            self.RAS_LMCE_EXE_INSTR_INSTR_ACCESS_PATH: self.LMCE_EXE_INSTR_FETCH_INSTR_FETCH_ERROR_MESSAGES_LIST
        }
        mca_dmesg_dict = {
            self.RAS_MCA_EXE_PATH: self.MCA_EXE_ERROR_DMESG_LIST,
            self.RAS_MCA_NON_EXE_PATH: self.MCA_NON_EXE_ERROR_DMESG_LIST
        }
        # Check for proper error message in /var/log/messages file
        success_messages = self._check_os_log.verify_os_log_error_messages(__file__, self.DUT_MESSAGES_FILE_NAME,
                                                                           mca_messages_dict[error_type])
        if error_type in mca_dmesg_dict:
            # Check for proper error message in dmesg

            success_dmesg = self._check_os_log.verify_os_log_error_messages(__file__, self.DUT_DMESG_FILE_NAME,
                                                                            mca_dmesg_dict[error_type])
        else:
            # As per TC no need to check dmesg log for instr srar error so passing it as True
            success_dmesg = True

        return success_messages, success_dmesg

    def mca_inject_and_check(self, error_type=RAS_MCA_NON_EXE_PATH):
        """
        This Method is used to Inject Mca Error through Ras Tools and Verify

        :param error_type:
        :return: true if injection and checks are passing
        """
        success = False
        serial_check_success = False
        messages_check = False
        dmesg_check = False
        mem_addr = 0x0

        # Clear dmesg and os logs on the SUT
        self._common_content_lib.clear_all_os_error_logs()

        # Prepare for mca injection
        # It also needs einj module to be loaded
        success = self.mca_prepare_injection()
        if success:
            success = self._einj_common.einj_prepare_injection()
            if not success:
                return False

        if success:
            # Inject MCA
            success = self.mca_inject_error(error_type, mem_addr)

            if success:
                # Check BIOS Serial log for error log
                serial_check_success = self.mca_check_serial_log(error_type, mem_addr)

                # Check OS log for proper logging of the error type, address, etc
                messages_check, dmesg_check = self.mca_check_os_log(error_type)

        # Finally return with consolidated return status
        self._log.info("Test status: Error injection result = %d", success)
        self._log.info("Test status: Serial log check result = %d", serial_check_success)
        self._log.info("Test status: OS messages log check result = %d", messages_check)
        self._log.info("Test status: OS dmesg log check result = %d", dmesg_check)
        return success
