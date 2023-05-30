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
import sys
import os
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.common_content_lib import CommonContentLib


class PythonSyserrCheckinTrustedState(TxtBaseTest):
    """
    Glasgow ID : 58216
    This Test case is check the system error on trusted state(TBOOT).
    This Test case is used to get the pci/cpu/mem information before Tboot and after Tboot.
    The value of pci/cpu/mem are compared individually before Tboot and after Tboot and value should not change.

    pre-requisites:
    1. Upgrade system to latest BKC.
    2. Attach a hard drive that has a POR Linux distro with tboot installed.
    3. Ensure that system has a TPM installed and provisioned with an ANY policy (capable of booting trusted)
    """
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    _FILE_NAME = "58216_cscript_log.txt"
    _PCI_CMD = "lspci"
    _CPU_CMD = "lscpu"
    _MEM_CMD = "lsmem"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance to check the system error in Tboot

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(
            PythonSyserrCheckinTrustedState,
            self).__init__(
            test_log,
            arguments,
            cfg_opts,
            self._BIOS_CONFIG_FILE)
        self._common_obj = CommonContentLib(self._log, self._os)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)
        self._klaxon = self._cscripts.get_cscripts_utils().get_klaxon_obj()
        self.log_file_path = self.get_csript_log_path()
        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()
        self.reboot_timeout = int(
            self._common_content_lib.get_sut_reboot_time_in_secs())
        self.tboot_index = None
        self.pre_tboot_pci = None
        self.pre_tboot_cpu = None
        self.pre_tboot_mem = None
        self.post_tboot_pci = None
        self.post_tboot_cpu = None
        self.post_tboot_mem = None

    def prepare(self):
        # type: () -> None
        """
        1. Execute OS commands before the Tboot set.
        2. Pre-validate whether sut is configured with Tboot by get the Tboot index in OS boot order.
        3. Load BIOS defaults settings.
        4. Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        """
        # get pre Tboot lsmem, lscpu and lspci data
        self.pre_tboot_mem = self._common_obj.execute_sut_cmd(
            self._MEM_CMD, "details of mem", self._command_timeout)
        self.pre_tboot_cpu = self._common_obj.execute_sut_cmd(
            self._CPU_CMD, "details of cpu", self._command_timeout)
        self.pre_tboot_pci = self._common_obj.execute_sut_cmd(
            self._PCI_CMD, "details of pci", self._command_timeout)

        # Get the Tboot_index from grub menu entry
        self.tboot_index = self.get_tboot_boot_position()
        self.set_default_boot_entry(
            self.tboot_index)  # Set Tboot as default boot
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self.reboot_timeout)  # To apply Bios changes
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def get_csript_log_path(self):
        """
        We are getting the Path for cscript log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self._FILE_NAME)
        return path

    def check_sys_error_get_log(self):
        """
        This function will check and save the system error output to file
        After saving the output, we are finding if any error is occurred.


        :return: if any error occurred return False else True
        """
        ret_val = False
        self._log.info("checking the sys errors")
        self._sdp.start_log(self.log_file_path, "w")
        self._klaxon.check_sys_errors()
        self._sdp.stop_log()
        with open(self.log_file_path, "r") as log_file:
            log_details = log_file.read()
            expected_error = re.findall(
                r"([0-9]\d*)\sError\sdetected\sin\s.*", log_details)
            if expected_error:  # This will remove the empty string
                for line in expected_error:
                    if int(line) > 0:
                        self._log.info("start of check sys errors details")
                        self._log.info(
                            "output of failed log is:{}".format(log_details))
                        self._log.info("End of check sys errors details")
                        log_error = "System has experienced some unexplained errors "
                        self._log.error(log_error)
                        break
                    else:
                        self._log.info(
                            "No errors detected after executing k.check_sys_errors()")
                        ret_val = True
        return ret_val

    def check_sys_error(self):
        """
        This function will execute Cscripts commands which is checking the system errors

        :return: If there is any unexplained error it will return false and TC fail
        """
        self._log.info(
            "Executing Cscripts commands for checking the system error...")
        self._log.info(self._sv.getAll())
        ret_err_cmd = self.check_sys_error_get_log()
        return ret_err_cmd

    def execute(self):
        """
        This function is used to check SUT boot with Tboot and
        compare results of lsmem, lscpu and lspci after Tboot.
        Check the system error in Tboot state. Ifany error make the TC fail.

        :return: True if Test case pass else fail
        """
        # verify if the system booted in Trusted mode.
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)
        self._os.reboot(self.reboot_timeout)  # To apply Bios changes
        if self.verify_trusted_boot():  # verify the sut boot with trusted env
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            return False

        # get post Tboot lsmem, lscpu and lspci data
        self.post_tboot_mem = self._common_obj.execute_sut_cmd(
            self._MEM_CMD, "details of mem", self._command_timeout)
        self.post_tboot_cpu = self._common_obj.execute_sut_cmd(
            self._CPU_CMD, "details of cpu", self._command_timeout)
        self.post_tboot_pci = self._common_obj.execute_sut_cmd(
            self._PCI_CMD, "details of pci", self._command_timeout)

        # Compare results of lsmem, lscpu and lspci before and after Tboot
        ret_sut_cmd_val = self.compare_mem_cpu_pci_data(
            self.pre_tboot_pci,
            self.post_tboot_pci,
            self.pre_tboot_cpu,
            self.post_tboot_cpu,
            self.pre_tboot_mem,
            self.post_tboot_mem)
        # Checking the system error using cscript
        ret_sys_error = self.check_sys_error()
        return ret_sut_cmd_val and ret_sys_error


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PythonSyserrCheckinTrustedState.main(
    ) else Framework.TEST_RESULT_FAIL)
