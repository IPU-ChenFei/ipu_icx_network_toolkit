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

import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class SdsiHqmIaxVerificationPowerManagementColdResetCycles(ContentBaseTestCase):
    """
    Glasgow_ID: 73959
    Phoenix_ID: 22012935790
    Verify MCE Logged Status, HQM by Performing Cold Reset Cycles and verifying status every cycle.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SdsiHqmIaxVerificationPowerManagementColdResetCycles object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SdsiHqmIaxVerificationPowerManagementColdResetCycles, self).__init__(test_log, arguments, cfg_opts)

        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs whether they updated properly.

        :return: None
        """
        self._log.info("Clear the CAP configurations already present.")
        self._sdsi_obj.erase_payloads_from_nvram()

        super(SdsiHqmIaxVerificationPowerManagementColdResetCycles, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self.reboot_cycles = 500

        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify the failure counters for CPU_{} after graceful G3.".format(cpu_counter + 1))
            license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(cpu_counter)
            payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(cpu_counter)

            assert license_key_auth_failures == 0, \
                "License key failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("License key authentication counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            assert payload_auth_fail_count == 0, \
                "CAP authentication failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("CAP authentication failure counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            self._log.info("Get the CPU PPIN/Hardware ID of the CPU.")
            cpu_ppin = self._sdsi_obj.get_cpu_hw_asset_id(cpu_counter)
            self._log.info("CPU PPIN/Hardware Asset ID of the CPU_{} is '{}'".format(cpu_counter + 1, cpu_ppin))

    def execute(self):
        """
        This test is Used to verify status of MCE, HQM, and IAX in Every Cold Reset of 50 Cycles'

        :return: True or False
        """
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU_{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU_{} before applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Get a the HQM4 CAP configuration for CPU_{}.".format(cpu_counter + 1))
            payload_info = self._sdsi_obj.get_capability_activation_payload(payload_name= "HQM4", socket=cpu_counter)

            self._log.info("Apply HQM4 configuration for CPU_{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_capability_activation_payload(payload_info, cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU_{} after applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info(
                "Verify the payload failure and ssku updates available counters are updated as expected for CPU_{}.".format(
                    cpu_counter + 1))
            assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU {}.".format(
                payload_fail_count_before, payload_fail_count_after, cpu_counter + 1)
            assert max_ssku_updates_before - 1 == max_ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU {}.".format(
                max_ssku_updates_before - 1, max_ssku_updates_after, cpu_counter + 1)

            self._log.info("Verify the CAP config is available for CPU_{}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_info[1],
                socket=cpu_counter), "CPU_{} is not provisioned after write operation. {} CAP information is not found.".format(
                cpu_counter + 1, payload_info[1])

            self._log.info("CAP config is applied successfully for CPU_{}.".format(cpu_counter + 1))

        self._log.info("Perform graceful g3.")
        self.perform_graceful_g3()

        self._log.info("Perform {} Cold reset cycles and verify the HQM4 data and MCE error in each cycles.".format(
            self.reboot_cycles))
        for cycle_number in range(self.reboot_cycles):
            self._log.info("Cold Reset cycle #{}.".format(cycle_number + 1))
            self._sdsi_obj.cold_reset()
            if self._common_content_lib.check_if_linux_mce_errors():
                log_error = "Machine Check errors are Logged in Cold Reset Cycle '{}'".format(cycle_number + 1)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("No Machine Check Errors are Logged in Cold Reset Cycle '{}'.".format(cycle_number + 1))
            self._log.info("Verify HQM4 data is available on the SUT in Cold Reset Cycle '{}'.".format(cycle_number + 1))
            assert self._sdsi_obj.verify_hqm_dlb_kernel("HQM4"), "HQM4 device information is not found in Cold Reset Cycle '{}'.".format(cycle_number + 1)
        self._log.info("Machine Check Events Status, HQM, IAX status is Verified in all {} Cold Reset Cycles.".format(self.reboot_cycles))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(SdsiHqmIaxVerificationPowerManagementColdResetCycles, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SdsiHqmIaxVerificationPowerManagementColdResetCycles.main() else Framework.TEST_RESULT_FAIL)
