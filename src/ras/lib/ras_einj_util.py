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
        "CPU","MEMORY CONTROLLER RD_CHANNEL",
         "MCi_ADDR register valid"]

    COMMERCIAL_EINJ_MEM_UC_NONFATAL_MESSAGES_LIST = \
        ["Transaction: Memory scrubbing error",
         "Hardware event",
         "Uncorrected error",
         "MemCtrl: Uncorrected patrol scrub error",
         "MCG status:RIPV"]

    COMMERCIAL_EINJ_MEM_UC_NONFATAL_DMESG_LIST = \
        ["UE memory scrubbing error",
         "Machine Check Exception"]

    # Uncorrectable fatal
    COMMERCIAL_EINJ_MEM_UC_FATAL_MESSAGES_LIST = \
        ["Transaction: Memory read error",
         "Hardware event",
         "Uncorrected error"]

    # Correctable
    EINJ_MEM_CE_MESSAGES_LIST = \
        ["ADDR 40001000",
         "Hardware event",
         "Corrected error"]

    EINJ_MEM_CE_DMESG_LIST = \
        ["CE memory read error",
         "Machine Check Event"]

    # Uncorrectable Non-fatal
    REF_EINJ_MEM_UC_NONFATAL_MESSAGES_LIST = \
        ["Transaction: Memory scrubbing error",
         "Hardware event",
         "Corrected error",
         "MemCtrl: Uncorrected patrol scrub error"]

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

    # Uncorrectable fatal
    COMMERCIAL_EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST = \
        ["event severity: recoverable",
         "section_type: PCIe error",
         "Hardware error"]

    COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST = \
        ["event severity: fatal",
         "section_type: PCIe error",
         "Hardware error"]

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

    DELAY_AFTER_EINJ_INJECTION_IN_SEC = 15
    DUT_MESSAGES_FILE_NAME = "messages"
    DUT_MESSAGES_PATH = "/var/log/" + DUT_MESSAGES_FILE_NAME

    DUT_JOURNALCTL_FILE_NAME = "journalctl"
    DUT_JOURNALCTL_NO_PROMPT = DUT_JOURNALCTL_FILE_NAME + " --no-pager"

    DUT_DMESG_FILE_NAME = "dmesg"
    DUT_RAS_TOOLS_FILE_NAME = "ras_tools"

    EINJ_MEM_CORRECTABLE = 0x00000008
    EINJ_MEM_UNCORRECTABLE_NONFATAL = 0x00000010
    EINJ_MEM_UNCORRECTABLE_FATAL = 0x00000020
    EINJ_PCIE_CORRECTABLE = 0x00000040
    EINJ_PCIE_UNCORRECTABLE_NONFATAL = 0x00000100
    EINJ_PCIE_UNCORRECTABLE_FATAL = 0x00000080
    WAITING_TIME_IN_SEC = 120

    def __init__(self, log, os, cfg_opts, common_content_lib, common_content_config_lib, rasp_pi=None):
        self._log = log
        self._os = os
        self._cfg = cfg_opts
        self._common_content_lib = common_content_lib
        self._common_content_config_lib = common_content_config_lib
        self._ac_power = rasp_pi
        self.cmd_timeout = self._common_content_config_lib.get_command_timeout()
        self._reboot_time =self._common_content_config_lib.get_reboot_timeout()
        self.journalctl_list = None
        self._ac_cycle_obj = RasCommonUtil(self._log, self._os, cfg_opts, self._common_content_config_lib)

    def einj_inject_and_check(self, error_type=EINJ_MEM_CORRECTABLE, viral=False,
                              failed_dimm_isolation_check=False):
        """
        Inject einj error and check logs

        :param error_type: einj error type
        :param viral: indicate if system is in viral mode
        :param failed_dimm_isolation_check: indicate whether to check failed dimm isolation info in logs
        :return: Boolean
        """
        try:
            serial_check_success = False
            os_log_check_success = False

            self._common_content_lib.clear_all_os_error_logs()
            success = self.einj_prepare_injection()  # Prepare for error injection

            if success:
                # Assigning the address for error injection
                if error_type == self.EINJ_MEM_CORRECTABLE:
                    mem_addr = 0x0000000040001000
                elif error_type == self.EINJ_MEM_UNCORRECTABLE_NONFATAL:
                    mem_addr = 0x0000000040002000
                elif error_type == self.EINJ_MEM_UNCORRECTABLE_FATAL:
                    mem_addr = 0x0000000040003000
                elif error_type == self.EINJ_PCIE_CORRECTABLE:
                    mem_addr = 0x0
                elif error_type == self.EINJ_PCIE_UNCORRECTABLE_NONFATAL:
                    mem_addr = 0x0
                elif error_type == self.EINJ_PCIE_UNCORRECTABLE_FATAL:
                    mem_addr = 0x0
                else:
                    self._log.error("Unknown error_type")
                    return False

                success = self.einj_inject_error(error_type, mem_addr)  # Inject the error
                if error_type == self.EINJ_MEM_UNCORRECTABLE_NONFATAL:
                    time.sleep(self.WAITING_TIME_IN_SEC)
                if not viral:
                    # Check BIOS Serial log for error log
                    serial_check_success = True
                    # Check OS log for proper logging of the error type, address, etc
                    os_log_check_success = self.einj_check_os_log(error_type,
                                                                  failed_dimm_isolation_check=
                                                                  failed_dimm_isolation_check)
            if not viral:
                # Finally return with consolidated return status
                self._log.info("Test status: Error injection result = %d", success)
                self._log.info("Test status: Serial log check result = %d", serial_check_success)
                self._log.info("Test status: OS log check result = %d", os_log_check_success)
                ret_value = success and serial_check_success and os_log_check_success
            else:
                ret_value = success
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
                ret_val = False
            else:
                self._log.info("einj module loaded successfully!!!")
                ret_val = True

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_val

    def einj_inject_error(self, error_type, address, viral=False, mask=0xfffffffffffff000, notrigger=0):
        """
        Setup einj for injection and inject

        :param error_type: einj var
        :param address: inj address
        :param viral:
        :param mask:
        :param notrigger:  1=no trigger- consumption from another source
        :return: Bool
        """
        try:
            inject_error_command = "nohup sudo /tmp/inject.sh &> inject.log"
            self._log.info("Injecting error through EINJ:")

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
                INJECTING_MEM_ERROR_COMMANDS_LIST = ["echo \"echo 0x%X > param1\" >> /tmp/inject.sh" % address,
                            "echo \"echo 0x%X > param2\" >> /tmp/inject.sh" % mask,
                            "echo \"echo 0x%X > error_type\" >> /tmp/inject.sh" % error_type,
                            "echo \"echo %d > notrigger\" >> /tmp/inject.sh" % notrigger,
                            "echo \"echo 1 > error_inject\" >> /tmp/inject.sh",
                            "sudo chmod 777 /tmp/inject.sh"
                            ]
                for mem_cmd in INJECTING_MEM_ERROR_COMMANDS_LIST:
                    command_result = self._os.execute(mem_cmd,
                                                      self.cmd_timeout)
                    if command_result.cmd_failed():
                        log_error = "Failed to run {} command with return value = '{}' and " \
                                    "std_error='{}'..".format(mem_cmd, command_result.return_code,
                                                              command_result.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)

                self._os.execute_async(inject_error_command)

                time.sleep(self.DELAY_AFTER_EINJ_INJECTION_IN_SEC)
                self._log.info("Injection completed ***************")
                self._log.info(command_result.stdout.strip())
                self._ac_cycle_obj.ac_cycle_if_os_not_alive(self._ac_power, auto_reboot_expected=True)
                ret_val = True
            elif pcie_error:
                INJECTING_PCIE_ERROR_COMMANDS_LIST = [
                    "echo \"echo 0x%X > param4\" >> /tmp/inject.sh" % address,
                    "echo \"echo 0x4 > flags\" >> /tmp/inject.sh",
                    "echo \"echo 0x%X > error_type\" >> /tmp/inject.sh" % error_type,
                    "echo \"echo 1 > error_inject\" >> /tmp/inject.sh",
                    "sudo chmod 777 /tmp/inject.sh"
                    ]
                for pci_cmd in INJECTING_PCIE_ERROR_COMMANDS_LIST:
                    command_result = self._os.execute(pci_cmd,
                                                      self.cmd_timeout)
                    if command_result.cmd_failed():
                        log_error = "Failed to run {} command with return value = '{}' and " \
                                    "std_error='{}'..".format(pci_cmd, command_result.return_code,
                                                              command_result.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                self._os.execute_async(inject_error_command)
                time.sleep(self.DELAY_AFTER_EINJ_INJECTION_IN_SEC)
                self._log.info("Injection completed ***************")
                if not viral:
                    self._ac_cycle_obj.ac_cycle_if_os_not_alive(self._ac_power, auto_reboot_expected=True)
                ret_val = True
            else:
                self._log.error("Unknown error type entered %d", error_type)
                ret_val = False
        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_val

    def einj_check_os_log(self, error_type, failed_dimm_isolation_check=False):
        """
        Check OS log for expected info

        :param error_type: einj var
        :param failed_dimm_isolation_check: indicate whether to check failed dimm isolation info in logs
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

            # #########################################################################################
            # MEM Correctable
            # MEM Uncorrectable NonFatal
            # MEM Uncorrectable Fatal
            #########################################################################################
            if error_type == self.EINJ_MEM_CORRECTABLE:
                message_list = self.EINJ_MEM_CE_MESSAGES_LIST
                dmesg_list = self.EINJ_MEM_CE_DMESG_LIST
                if failed_dimm_isolation_check:
                    self.journalctl_list = self.EINJ_MEM_CE_FAILED_DIMM_ISOLATION_JOURNALCTL_LIST
                    message_list = None
                    dmesg_list = None
            elif error_type == self.EINJ_MEM_UNCORRECTABLE_NONFATAL:
                message_list = self.REF_EINJ_MEM_UC_NONFATAL_MESSAGES_LIST
                dmesg_list = self.REF_EINJ_MEM_UC_NONFATAL_DMESG_LIST
                if failed_dimm_isolation_check:
                    self.journalctl_list = self.EINJ_MEM_UC_NONFATAL_FAILED_DIMM_ISOLATION_JOURNALCTL_LIST
                    message_list = None
                    dmesg_list = None
            elif error_type == self.EINJ_MEM_UNCORRECTABLE_FATAL:
                message_list = self.COMMERCIAL_EINJ_MEM_UC_FATAL_MESSAGES_LIST
                self.journalctl_list = None
                dmesg_list = None  # No dmesh check as system will reboot and clean dmesg
            #########################################################################################
            # PCIE Correctable
            # PCIE Uncorrectable NonFatal
            # PCIE Uncorrectable Fatal
            #########################################################################################
            elif error_type == self.EINJ_PCIE_CORRECTABLE:
                message_list = self.COMMERCIAL_EINJ_PCIE_CE_MESSAGES_LIST
                self.journalctl_list = None
                dmesg_list = self.COMMERCIAL_EINJ_PCIE_CE_DMESG_LIST
            elif error_type == self.EINJ_PCIE_UNCORRECTABLE_NONFATAL:
                message_list = self.COMMERCIAL_EINJ_PCIE_UC_NONFATAL_MESSAGES_LIST
                self.journalctl_list = None
                dmesg_list = None
            elif error_type == self.EINJ_PCIE_UNCORRECTABLE_FATAL:
                message_list = self.COMMERCIAL_EINJ_PCIE_UC_FATAL_MESSAGES_LIST
                self.journalctl_list = None
                dmesg_list = None
            else:
                self._log.error("Unknown error_type")
                return False

            # Check for proper error message in /var/log/messages file
            if message_list is not None:
                success_messages = self.verify_os_log_error_messages(
                    self.DUT_MESSAGES_FILE_NAME, message_list)

            # Check for proper error message in system journal
            if self.journalctl_list is not None:
                success_journalctl = self.verify_os_log_error_messages(
                    self.DUT_JOURNALCTL_FILE_NAME, self.journalctl_list)

            # Check for proper error message in dmesg
            if dmesg_list is not None:
                success_dmesg = self.verify_os_log_error_messages(
                    self.DUT_DMESG_FILE_NAME, dmesg_list)

            ret_val = success_messages or success_journalctl or success_dmesg
        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_val

    def verify_os_log_error_messages(self, dut_os_error_log_file_name,
                                     passed_error_signature_list_to_parse, error_signature_list_to_log=None):
        """
        Transfer os logs using SSH and verify error signatures are present for given error log and error type

        :param dut_os_error_log_file_name: Error log file name, i.e. messages or dmesg_file
        :param passed_error_signature_list_to_parse: test error signature to verify in a list form
        :param error_signature_list_to_log: signature strings to place in test log(typical=mcelog)
        :return: True if os logs were transferred to host and given error signature was discovered, false otherwise
        """
        try:
            if error_signature_list_to_log is None:
                error_signature_list_to_log = []
            if not passed_error_signature_list_to_parse:
                raise ValueError("Error message list to parse is empty")
            if type(error_signature_list_to_log) != list:
                raise ValueError("Error_signature_list_to_log was not a list as expected")

            # Create copy of passed in list to ensure function is non-destructive to original!
            if type(passed_error_signature_list_to_parse) != list:
                error_signature_list_to_parse = [passed_error_signature_list_to_parse]
            else:
                error_signature_list_to_parse = list(passed_error_signature_list_to_parse)

            # Create the appropriate message file either from ras_tools or os to check key words
            os_log_cmd_mapping_dictionary = {self.DUT_MESSAGES_FILE_NAME: "cat " + self.DUT_MESSAGES_PATH,
                                             self.DUT_JOURNALCTL_FILE_NAME: self.DUT_JOURNALCTL_FILE_NAME + " "
                                                                                                            "--no-pager",
                                             self.DUT_DMESG_FILE_NAME: self.DUT_DMESG_FILE_NAME,
                                             self.DUT_RAS_TOOLS_FILE_NAME: "cat exe.log"}
            try:
                os_log_cmd_to_execute = os_log_cmd_mapping_dictionary[dut_os_error_log_file_name]
            except KeyError:
                raise ValueError("Invalid or unknown OS error log specified")

            output_file_log = self._os.execute(os_log_cmd_to_execute, self.cmd_timeout)
            self._log.info("%s", output_file_log.stdout.strip())

            self._log.info("Check " + dut_os_error_log_file_name + " file content after error injection")
            print(dut_os_error_log_file_name, "File_name_of_dut")
            found = 0
            for string_to_look in error_signature_list_to_parse:
                self._log.info("++++++++++++ Looking for [%s]", string_to_look)
                if re.findall(string_to_look, output_file_log.stdout.strip(), re.IGNORECASE | re.MULTILINE):
                    self._log.info("    ++++ String found")
                    found = found + 1
                else:
                    self._log.error("    ---- String Not found")

            if found == len(error_signature_list_to_parse):
                self._log.info("All the strings from the list are found")
                self._log.info("exp %d act %d", len(error_signature_list_to_parse), found)
                verified_os_log_error_messages_bool = True
            else:
                self._log.error("All the strings from the list are NOT found")
                self._log.info("exp %d act %d", len(error_signature_list_to_parse), found)
                verified_os_log_error_messages_bool = False

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return verified_os_log_error_messages_bool
