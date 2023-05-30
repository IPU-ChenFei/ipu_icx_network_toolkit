#!/usr/bin/env python
#################################################################################
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
#################################################################################


import re
import time

from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.ras.lib.ras_common_utils import RasCommonUtil


class RasEinjCommon(object):
    """
    This Class is used as Common Class for all RasEinjCommon
    """
    PFA_PAGE_OFFLINE_MEM_CE_MESSAGES_LIST = \
        ["Transaction: Memory read error"
         "Offlining page"
         "Hardware event",
         "Corrected error",
         "CPU", "MEMORY CONTROLLER RD_CHANNEL",
         "MCi_ADDR register valid"]

    # Correctable
    EINJ_MEM_CE_MESSAGES_LIST = \
        ["ADDR 40001000",
         "Hardware event",
         "Corrected error"]

    EINJ_MEM_CE_DMESG_LIST = \
        ["Hardware Error",
         "event severity: corrected",
         "section_type: memory error"]

    # Uncorrectable Non-fatal
    REF_EINJ_MEM_UC_NONFATAL_MESSAGES_LIST = \
        ["event severity: recoverable",
         "Uncorrected error",
         "Hardware Error"]

    REF_EINJ_MEM_UC_NONFATAL_DMESG_LIST = \
        ["severity: corrected",
         "Machine Check Event"]

    EINJ_MEM_UC_NONFATAL_FAILED_DIMM_ISOLATION_JOURNALCTL_LIST = \
        ["Hardware Error",
         "Uncorrected error",
         "physical_address: 0x0000000040002000",
         "node:",
         "card:",
         "module:",
         "rank:",
         "bank:"]

    # Correctable
    EINJ_MEM_CE_FAILED_DIMM_ISOLATION_JOURNALCTL_LIST = \
        ["Hardware Error",
         "severity: corrected",
         "physical_address: 0x0000000040001000",
         "node:",
         "card:",
         "module:",
         "rank:",
         "bank:"]

    # Uncorrectable non fatal

    COMMERCIAL_EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST = \
        ["event severity: fatal",
         "section_type: PCIe error",
         "port_type: 4, root port"]

    # below added because a UCE-NF error has different messaging if eDPC is enabled.
    EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST_WITH_EDPC = \
         ["severity=Uncorrected",
          "unmasked uncorrectable error detected",
          "(Non-Fatal)"]

    REF_EINJ_PCIE_UC_NONFATAL_DMESG_LIST = COMMERCIAL_EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST

    # Uncorrectable fatal

    COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST = \
        ["event severity: fatal",
         "section_type: PCIe error",
         "port_type: 4, root port"]

    # not used as there is issue with mcelog, so we only check upper OS kernel messge
    COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST_Not_used = \
        ["Generic Generic IO Request-did-not-timeout",
         "IO MCA reported by root port",
         "Hardware event",
         "Uncorrected error"]

    # Correctable
    COMMERCIAL_EINJ_PCIE_CE_MESSAGES_LIST = \
        ["section_type: PCIe error",
         "event severity: corrected",
         "Hardware error"]

    COMMERCIAL_EINJ_PCIE_CE_DMESG_LIST = \
        ["section_type: PCIe error",
         "event severity: corrected",
         "Hardware error"]

    DUT_MESSAGES_FILE_NAME = "messages"
    DUT_MESSAGES_PATH = "/var/log/" + DUT_MESSAGES_FILE_NAME

    DUT_JOURNALCTL_FILE_NAME = "journalctl"
    DUT_JOURNALCTL_NO_PROMPT = DUT_JOURNALCTL_FILE_NAME + " --no-pager"

    DUT_DMESG_FILE_NAME = "dmesg"
    DUT_RAS_TOOLS_FILE_NAME = "ras_tools"

    RUNNER_EINJ_PATH = "/runner/bin/scripts"
    LINUX_ERROR_MASK = r'0xfffffffffffff000'
    CHECK_RUNNER_EXECUTION_STATUS = "Status : PASSED"
    RUNNER_EINJ_CE_ERROR_INJECT_CMD = "python2 run-rasrunner.py -i 0x008 -m " + LINUX_ERROR_MASK \
                                      + " -a {} -t 0:0:01"
    RUNNER_EINJ_UCE_ERROR_INJECT_CMD = "python2 run-rasrunner.py -i 0x010 -m " + LINUX_ERROR_MASK \
                                      + " -a {} -t 0:0:01"
    APCI_EINJ_CE_ERROR_INJECT_RUNNER_CMD = "python2 run-rasrunner.py -i 0x008 -m " + LINUX_ERROR_MASK \
                                           + " -a {} -t 0:0:01"
    EINJ_MEM_CORRECTABLE = 0x00000008
    EINJ_MEM_UNCORRECTABLE_NONFATAL = 0x00000010
    EINJ_MEM_UNCORRECTABLE_FATAL = 0x00000020
    EINJ_PCIE_CORRECTABLE = 0x00000040
    EINJ_PCIE_UNCORRECTABLE_NONFATAL = 0x00000080
    EINJ_PCIE_UNCORRECTABLE_NONFATAL_EDPC = 0x00000085
    EINJ_PCIE_UNCORRECTABLE_FATAL = 0x00000100
    EINJ_MEM_ADDR_OFFSET = 0x1000

    EINJ_MEM_UC_FATAL_MESSAGES_LIST = \
        [r"Hardware\sError",
         r"event\sseverity\:\sfatal",
         r"Error\s\d\,\stype\:\sfatal",
         r"section\_type\:\smemory\serror"
         ]

    EINJ_PCIE_UC_FATAL_DMESG_LIST = COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST
    EINJ_PCIE_CE_JOURNALCTL_LIST = COMMERCIAL_EINJ_PCIE_CE_MESSAGES_LIST
    EINJ_PCIE_UC_NONFATAL_JOURNALCTL_LIST = COMMERCIAL_EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST
    EINJ_PCIE_UC_FATAL_JOURNALCTL_LIST = COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST

    EINJ_MESSAGES_DICT = {
        EINJ_MEM_CORRECTABLE: EINJ_MEM_CE_MESSAGES_LIST,
        EINJ_MEM_UNCORRECTABLE_NONFATAL: REF_EINJ_MEM_UC_NONFATAL_MESSAGES_LIST,
        EINJ_MEM_UNCORRECTABLE_FATAL: EINJ_MEM_UC_FATAL_MESSAGES_LIST,
        EINJ_PCIE_CORRECTABLE: COMMERCIAL_EINJ_PCIE_CE_MESSAGES_LIST,
        EINJ_PCIE_UNCORRECTABLE_NONFATAL: COMMERCIAL_EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST,
        EINJ_PCIE_UNCORRECTABLE_NONFATAL_EDPC: EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST_WITH_EDPC,
        EINJ_PCIE_UNCORRECTABLE_FATAL: COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST,
    }

    EINJ_DMESG_DICT = {
        EINJ_MEM_CORRECTABLE: EINJ_MEM_CE_DMESG_LIST,
        EINJ_MEM_UNCORRECTABLE_NONFATAL: REF_EINJ_MEM_UC_NONFATAL_MESSAGES_LIST,
        EINJ_PCIE_CORRECTABLE: COMMERCIAL_EINJ_PCIE_CE_DMESG_LIST,
        EINJ_MEM_UNCORRECTABLE_FATAL: None,
        EINJ_PCIE_UNCORRECTABLE_FATAL: EINJ_PCIE_UC_FATAL_DMESG_LIST,
        EINJ_PCIE_UNCORRECTABLE_NONFATAL: REF_EINJ_PCIE_UC_NONFATAL_DMESG_LIST,
        EINJ_PCIE_UNCORRECTABLE_NONFATAL_EDPC: EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST_WITH_EDPC,
    }

    EINJ_JOURNALCTL_DICT = {
        EINJ_MEM_CORRECTABLE: EINJ_MEM_CE_FAILED_DIMM_ISOLATION_JOURNALCTL_LIST,
        EINJ_MEM_UNCORRECTABLE_NONFATAL: EINJ_MEM_UC_NONFATAL_FAILED_DIMM_ISOLATION_JOURNALCTL_LIST,
        EINJ_MEM_UNCORRECTABLE_FATAL: None,
        EINJ_PCIE_CORRECTABLE: EINJ_PCIE_CE_JOURNALCTL_LIST,
        EINJ_PCIE_UNCORRECTABLE_NONFATAL: EINJ_PCIE_UC_NONFATAL_JOURNALCTL_LIST,
        EINJ_PCIE_UNCORRECTABLE_FATAL: EINJ_PCIE_UC_FATAL_JOURNALCTL_LIST,
        EINJ_PCIE_UNCORRECTABLE_NONFATAL_EDPC: EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST_WITH_EDPC,
    }

    def __init__(self,
                 log, os, common_content_lib, common_content_config_lib, rasp_pi=None, cfg_opts=None):
        self._log = log
        self._os = os
        self._common_content_lib = common_content_lib
        self._common_content_config_lib = common_content_config_lib
        self._ac_power = rasp_pi
        self.cmd_timeout = self._common_content_config_lib.get_command_timeout()
        self._reboot_timeout = self._common_content_config_lib.get_reboot_timeout()
        self._wait_time_in_sec = self._common_content_config_lib.itp_halt_time_in_sec()
        self._ac_timeout_delay_in_sec = self._common_content_config_lib.ac_timeout_delay_in_sec()
        self._einj_mem_addr = self._common_content_config_lib.einj_mem_default_address()
        self._einj_pcie_bridge_list = self._common_content_config_lib.get_pcie_bridge_values()
        self._acpi_einj_runner_ce_address = self._common_content_config_lib.acpi_einj_runner_ce_addr()
        self._common_content_config = ContentConfiguration(self._log)
        self.journalctl_list = None
        self._waiting_time_after_injecting_uncorr_error = self._common_content_config_lib. \
            waiting_time_after_injecting_uncorr_error()
        self._default_mask = self._common_content_config_lib.default_mask_value()
        self._os_log_verify = OsLogVerifyCommon(self._log, self._os, self._common_content_config_lib,
                                                self._common_content_lib)
        self._cfg = cfg_opts
        self.edpc_and_os_native_flags_offset = 5  # signal eDPC or OS native AER by adding 5 to the dictionary index
                                                # of the legacy mode test

    def error_injection_list(self, error_type):
        """
            This method returns the corresponding error list based on the error type
            :return Returns error list
        """
        RUNNER_EINJ_ERROR_LIST = []
        if error_type == "correctable_oob":
            self._phy_addr = self._common_content_config.einj_runner_ce_addr()
            RUNNER_EINJ_ERROR_LIST = ["Hardware Error",
                                      "event severity: corrected",
                                      "physical_address: {}".format(self._phy_addr),
                                      "node:",
                                      "card:",
                                      "module:",
                                      "rank:"]
        elif error_type == "correctable_acpi":
            self._phy_addr = self._common_content_config.acpi_einj_runner_ce_addr()
            RUNNER_EINJ_ERROR_LIST = ["Hardware Error",
                                      "event severity: corrected",
                                      "physical_address: {}".format(self._phy_addr),
                                      "section_type: memory error"]
        elif error_type == "uncorrectable_oob":
            self._phy_addr = self._common_content_config.einj_runner_uce_addr()
            RUNNER_EINJ_ERROR_LIST = ["Hardware Error",
                                      "event severity: recoverable",
                                      "physical_address: {}".format(self._phy_addr)]
        return RUNNER_EINJ_ERROR_LIST

    def einj_inject_and_check(self, error_type=EINJ_MEM_CORRECTABLE, loops_count=1,
                              viral=False, failed_dimm_isolation_check=False, edpc_en=False, address=None):
        """
        Inject einj error and check logs

        :param error_type: einj error type
        :param loops_count: parameter for how many inject and check iterations to execute
        :param viral: indicate if system is in viral mode
        :param failed_dimm_isolation_check: indicate whether to check failed dimm isolation info in logs
        :param edpc_en: boolean for whether eDPC is set in the BIOS, Needed for cases where signalling changes
        :return: Boolean
        """
        try:
            serial_check_success = False
            os_log_check_success = False
            ret_value = False

            success = self.einj_prepare_injection()  # Prepare for error injection

            if success:
                # Assigning the address for error injection
                if error_type == self.EINJ_MEM_CORRECTABLE:
                    address = self._einj_mem_addr
                elif error_type == self.EINJ_MEM_UNCORRECTABLE_NONFATAL:
                    address = self._einj_mem_addr + self.EINJ_MEM_ADDR_OFFSET
                elif error_type == self.EINJ_MEM_UNCORRECTABLE_FATAL:
                    address = self._einj_mem_addr + 2 * self.EINJ_MEM_ADDR_OFFSET
                elif error_type == self.EINJ_PCIE_CORRECTABLE or error_type == self.EINJ_PCIE_UNCORRECTABLE_NONFATAL \
                        or error_type == self.EINJ_PCIE_UNCORRECTABLE_FATAL:
                    address = address
                else:
                    self._log.error("Unknown error_type")
                    return False

                for i in range(0, loops_count):
                    self._log.info("Starting loop %d", i)
                    try:
                        self._common_content_lib.clear_all_os_error_logs()
                    except RuntimeError as e:
                        self._log.error("failed to clear the logs, error is %s", str(e))
                    success = self.einj_inject_error(error_type, address)  # Inject the error
                    if error_type == self.EINJ_MEM_UNCORRECTABLE_NONFATAL:
                        time.sleep(self._waiting_time_after_injecting_uncorr_error)
                    if not viral:
                        # Check BIOS Serial log for error log
                        serial_check_success = True
                        # Check OS log for proper logging of the error type, address, etc
                        os_log_check_success = self.einj_check_os_log(error_type,
                                                                      failed_dimm_isolation_check
                                                                      =failed_dimm_isolation_check, edpc_en=edpc_en)

                        # Finally return with consolidated return status
                        self._log.info("Test status: Error injection result = %d", success)
                        self._log.info("Test status: Serial log check result = %d", serial_check_success)
                        self._log.info("Test status: OS log check result = %d", os_log_check_success)
                        ret_value = success and serial_check_success and os_log_check_success
                    else:
                        ret_value = success
                    if not ret_value:
                        self._log.error("Test failed at loop %d", i)
                        return False
        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_value

    def einj_prepare_injection(self):
        """
        Prepare SUT fro EINJ error injection

        :return: Bool
        """
        try:
            # Update the date to ensure injection logging can occur properly
            self._log.info("Updating date to ensure proper error logging")
            self._common_content_lib.set_datetime_on_sut()

            # Load einj module to check whether error injection related BIOS knobs are enabled or not
            self._log.info("Mounting debugFS...")
            self._os.execute("mount -t debugfs none /sys/kernel/debug", self.cmd_timeout)

            self._log.info("Loading einj module:")
            result = self._os.execute("sudo modprobe einj", self.cmd_timeout)
            self._log.info(result.stdout)
            # Check if the load was successful or not
            if re.match(r"modprobe: FATAL:", result.stdout):
                self._log.error("einj module cannot be loaded - Check BIOS knob setting - Exiting the test!!!")
                return False
            else:
                self._log.info("einj module loaded successfully!!!")
                return True

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def inject_mem_and_pcie_errors(self, inject_error_commands_list):
        """
        This Method is used to Inject Memory or Pcie Error

        :param inject_error_commands_list: Injects Memory or Pcie Error.
        """
        for command in inject_error_commands_list:
            command_result = self._os.execute(command, self.cmd_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run {} command with return value = '{}' and " \
                            "std_error='{}'..".format(command, command_result.return_code,
                                                      command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

        inject_file_content = self._common_content_lib.execute_sut_cmd("cat inject.sh", "check inject file", self.cmd_timeout, cmd_path="/tmp")
        self._log.info("inject.sh file content is \n{}".format(inject_file_content))
        cmd_to_inject_error = r"nohup sudo /tmp/inject.sh".strip()
        # Using Async to inject the error to run test in back ground to avoid from getting stuck.
        self._os.execute_async(cmd_to_inject_error)

    def einj_inject_error(self, error_type, address, viral=False, notrigger=0):
        """
        Setup einj for injection and inject

        :param error_type: einj_var used to differentiate between mem errors and pcie errors
        :param address: Error Injection Address
        :param viral: Describes whether viral state is Enabled or Not
        :param notrigger:  1=no trigger- consumption from another source
        :return: Bool
        """
        try:
            ras_common_util_obj = RasCommonUtil(self._log, self._os, self._cfg, self._common_content_config_lib)
            mask = self._default_mask
            self._log.info("Inject error through EINJ:")

            command_result = self._os.execute("sudo rm -rf /tmp/inject.sh; touch /tmp/inject.sh", self.cmd_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run 'touch /tmp/inject.sh' command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            command_result = self._os.execute("echo \"cd /sys/kernel/debug/apei/einj\" > /tmp/inject.sh",
                                              self.cmd_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run the command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            mem_error = (error_type == self.EINJ_MEM_CORRECTABLE) | \
                        (error_type == self.EINJ_MEM_UNCORRECTABLE_NONFATAL) | \
                        (error_type == self.EINJ_MEM_UNCORRECTABLE_FATAL)

            pcie_error = (self.EINJ_PCIE_CORRECTABLE == error_type) | \
                         (self.EINJ_PCIE_UNCORRECTABLE_NONFATAL == error_type) | \
                         (self.EINJ_PCIE_UNCORRECTABLE_FATAL == error_type)

            if mem_error:
                INJECT_MEM_ERROR_CMDS_LIST = ["echo \"echo 0x%X > param1\" >> /tmp/inject.sh" % address,
                                              "echo \"echo 0x%X > param2\" >> /tmp/inject.sh" % mask,
                                              "echo \"echo 0x%X > error_type\" >> /tmp/inject.sh" % error_type,
                                              "echo \"echo %d > notrigger\" >> /tmp/inject.sh" % notrigger,
                                              "echo \"echo 1 > error_inject\" >> /tmp/inject.sh",
                                              "sudo chmod 777 /tmp/inject.sh"
                                              ]
                self.inject_mem_and_pcie_errors(INJECT_MEM_ERROR_CMDS_LIST)

                time.sleep(self._wait_time_in_sec)
                self._log.info("Injection completed")
                self._log.info(command_result.stdout.strip())
                if not viral:
                    if not self._os.is_alive():
                        ras_common_util_obj.ac_cycle_if_os_not_alive(self._ac_power, auto_reboot_expected=True)

                return True
            elif pcie_error:
                INJECT_PCIE_ERROR_CMDS_LIST = [
                    "echo \"echo {} > param4\" >> /tmp/inject.sh".format(address),
                    "echo \"echo 0x4 > flags\" >> /tmp/inject.sh",
                    "echo \"echo 0x%X > error_type\" >> /tmp/inject.sh" % error_type,
                    "echo \"echo 1 > error_inject\" >> /tmp/inject.sh",
                    "sudo chmod 777 /tmp/inject.sh"
                ]
                self.inject_mem_and_pcie_errors(INJECT_PCIE_ERROR_CMDS_LIST)

                time.sleep(self._wait_time_in_sec)
                self._log.info("Injection completed")

                if not viral:
                    if not self._os.is_alive():
                        ras_common_util_obj.ac_cycle_if_os_not_alive(self._ac_power, auto_reboot_expected=True)
                return True
            else:
                self._log.error("Unknown error type entered %d", error_type)
                return False
        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def einj_check_os_log(self, error_type, failed_dimm_isolation_check=False, edpc_en=False):
        """
        Check OS log for expected info
        :param error_type: einj var
        :param failed_dimm_isolation_check:  indicate whether to check failed dimm isolation info in logs
        :param edpc_en: boolean for whether eDPC is set in the BIOS, Needed for cases where signalling changes
        :return: Bool
        """
        success_messages = False
        success_journalctl = False
        success_dmesg = False
        try:
            self._log.info("messages Log Content after error injection:")
            result_log = self._os.execute("sudo cat " + self.DUT_MESSAGES_PATH, self.cmd_timeout)
            self._log.info(result_log.stdout.strip())

            self._log.info("journalctl Log Content after error injection:")
            result_log = self._os.execute(self.DUT_JOURNALCTL_NO_PROMPT, self.cmd_timeout)
            self._log.info(result_log.stdout.strip())

            self._log.info("dmesg Log Content after error injection:")
            result_dmesg = self._os.execute(self.DUT_DMESG_FILE_NAME, self.cmd_timeout)
            self._log.info(result_dmesg.stdout.strip())

            self._log.info("OS Log Check")

            if edpc_en:
                error_type += self.edpc_and_os_native_flags_offset
                self._log.info("Testing with eDPC messaging")

            # Check for proper error message in /var/log/messages file
            if self.EINJ_MESSAGES_DICT[error_type]:
                success_messages = self._os_log_verify.verify_os_log_error_messages(__file__,
                                                                                    self.DUT_MESSAGES_FILE_NAME,
                                                                                    self.EINJ_MESSAGES_DICT[error_type])

            # Check for proper error message in system journal
            if self.EINJ_JOURNALCTL_DICT[error_type]:
                success_journalctl = self._os_log_verify.verify_os_log_error_messages(__file__,
                                                                                      self.DUT_JOURNALCTL_FILE_NAME,
                                                                                      self.EINJ_JOURNALCTL_DICT[
                                                                                          error_type])
            # Check for proper error message in dmesg
            if self.EINJ_DMESG_DICT[error_type]:
                success_dmesg = self._os_log_verify.verify_os_log_error_messages(__file__,
                                                                                 self.DUT_DMESG_FILE_NAME,
                                                                                 self.EINJ_DMESG_DICT[error_type])

            return success_messages or success_journalctl or success_dmesg

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def einj_pcie_error_addr_sec_bus(self, pcie_bridge_value):
        """
        Calculating the pcie card address based on pcie bridge value
        :param pcie_bridge_value: einj var

        :return: hex number of error address
        """
        seg_value = 0
        reserved_value = '00000000'
        bus_list = []
        device_value = 0
        try:
            bridge_list = re.sub(r"[:.]", "\n", pcie_bridge_value)
            # Separates the bdf root structure to individual values into a list
            bridge_values_list = bridge_list.split("\n")
            # Converts the bus values to binary of 4 bits individually
            bus_list = [bin(int(a)).replace("0b", "") for a in str(bridge_values_list[0])]
            bus_list = [str("0" * (4 - len(str(a)))) + str(a) for a in bus_list]
            # Converts the device value to binary of 5 bits
            device_value = bin(int(bridge_values_list[1])).replace("0b", "")
            if len(str(device_value)) < 5:
                device_value = str("0" * (5 - len(str(device_value)))) + str(device_value)
            # Converts the function value to binary of 3 bits
            function_value = bin(int(bridge_values_list[2])).replace("0b", "")
            if len(str(function_value)) < 3:
                function_value = str("0" * (3 - len(str(function_value)))) + str(function_value)
            # Appends all the binary values in str format to single value
            res = (str(seg_value) + "".join(bus_list) + str(device_value) + str(function_value) + str(reserved_value))
            # convert str to hexadecimal
            address = hex(int(res, 2))
            return address

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
