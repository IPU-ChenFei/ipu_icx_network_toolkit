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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class SDSIVerifyDataStoredInS3MNvram(ContentBaseTestCase):
    """
    Glasgow_ID: 69593
    Phoenix_ID: 18014075188
    This test verifies that the SDSI NVRAM Data Structure for each populated CPU contains data as expected after provisioning.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SDSIVerifyDataStoredInS3MNvram

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SDSIVerifyDataStoredInS3MNvram, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power,
                                       cfg_opts)

        # self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self.os)  # type: CpuInfoProvider
        # self._cpu_info_provider.populate_cpu_info()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""

        self._log.info("Clear any existing payloads from the CPU")
        self._sdsi_obj.erase_payloads_from_nvram()

        super(SDSIVerifyDataStoredInS3MNvram, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self._log.info("Number of sockets connected on the platform is : {}".format(self._sdsi_obj.number_of_cpu))

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
            1.	Write the licence key certificate to the SUT.
            2.	Make sure your CPU has been provisioned previously with the execution of test case.
            3.	If not, write a payload configuration to the SUT.
            4.	Verify the SDSI NVRAM Data Structure for each populated CPU contains data as expected after provisioning.
        """
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info("Write a payload configuration to the SUT for CPU {}.".format(cpu_counter + 1))
            # Specify payload_name=None for random payload apply.
            payload_info = self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter)
            self._sdsi_obj.apply_capability_activation_payload(payload_info, cpu_counter)
            payload_name = payload_info[1]

            self._log.info(
                "Verify the capability activation payload {} is available on the NVRAM for CPU {}.".format(payload_name,
                                                                                                           cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(payload_name=payload_name, socket=cpu_counter), \
                "CPU is not provisioned after the write operation. Payload information for {} is not found." \
                    .format(payload_name)

            self._log.info("Capability activation payload {} is applied successfully for CPU {}.".format(payload_name,
                                                                                                         cpu_counter + 1))

        self._log.info("Reboot the SUT for the changes to take effect.")
        self._sdsi_obj.perform_graceful_powercycle()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify SDSi is enabled for CPU {}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_sdsi_enabled(socket=cpu_counter), "SDSi enabled value is mismatching."

            self._log.info(
                "Verify the CPU Hardware ID and CPU PPIN value of all the payloads are same for CPU {}.".format(
                    cpu_counter + 1))
            cpu_hw_id = self._sdsi_obj.get_cpu_hw_asset_id(socket=cpu_counter)
            cpu_ppin = self._sdsi_obj.cpu_hw_info[cpu_counter]['ppin']
            assert all(ppin[2:] == cpu_hw_id for ppin in cpu_ppin), "CPU HW ID is not matching with PPIN."

            self._log.info(
                "Verify the max ssku updates and ssku updates remaining values are equal and are equal to 2 for CPU {}.".format(
                    cpu_counter + 1))
            max_ssku_updates = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            assert max_ssku_updates == 2, "Maximum allowed ssku updates should be 2, but found {}.".format(
                max_ssku_updates)
            assert max_ssku_updates == ssku_updates_available, "Maximum ssku updates should be equal to ssku updates available after the cold reboot. But found, Maximum ssku updates = {} and ssku updates available = {}.".format(
                max_ssku_updates, ssku_updates_available)

            self._log.info("Verify the license key auth fail counters for CPU {} is 0.".format(cpu_counter + 1))
            license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(cpu_counter)
            payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(cpu_counter)
            assert (
                    license_key_auth_failures == 0 and payload_auth_fail_count == 0), "Authentication key failure counter is not reset to 0 after after powercycle on CPU {}.".format(
                cpu_counter + 1)
            self._log.info("Verify the max license key auth fail counters for CPU {} is 2.".format(cpu_counter + 1))
            max_license_key_auth_failures = self._sdsi_obj.get_max_license_key_auth_fail_count(cpu_counter)
            max_payload_auth_fail_count = self._sdsi_obj.get_max_license_auth_fail_count(cpu_counter)
            assert (
                    max_license_key_auth_failures == 2 and max_payload_auth_fail_count == 2), "Authentication key failure counter should be 2 on CPU {}, but found, Max Payload authentication counter = {} and max License key auth failures = {}.".format(
                cpu_counter + 1, max_license_key_auth_failures, max_payload_auth_fail_count)

            self._log.info("Verify the License content type has a non-zero value for CPU_{}.".format(cpu_counter + 1))
            content_type = self._sdsi_obj.get_content_type(socket=cpu_counter)
            assert content_type != 0, "License content type should be a non-zero value. But the value is {} for CPU_{}.".format(
                content_type, cpu_counter + 1)

            self._log.info("Verify the License region rev id has a non-zero value for CPU_{}.".format(cpu_counter + 1))
            region_rev_id = self._sdsi_obj.get_region_rev_id(socket=cpu_counter)
            assert region_rev_id != 0, "License region rev id should be a non-zero value. But the value is {} for CPU_{}.".format(
                region_rev_id, cpu_counter + 1)

            self._log.info("Verify the License header size has a non-zero value for CPU_{}.".format(cpu_counter + 1))
            header_size = self._sdsi_obj.get_header_size(socket=cpu_counter)
            assert header_size != 0, "License header size should be a non-zero value. But the value is {} for CPU_{}.".format(
                header_size, cpu_counter + 1)

            self._log.info("Verify the License total size has a non-zero value for CPU_{}.".format(cpu_counter + 1))
            total_size = self._sdsi_obj.get_total_size(socket=cpu_counter)
            assert total_size != 0, "License total size should be a non-zero value. But the value is {} for CPU_{}.".format(
                total_size, cpu_counter + 1)

            self._log.info("Verify the License key size has a non-zero value for CPU_{}.".format(cpu_counter + 1))
            key_size = self._sdsi_obj.get_key_size(socket=cpu_counter)
            assert key_size != 0, "License key size should be a non-zero value. But the value is {} for CPU_{}.".format(
                key_size, cpu_counter + 1)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(SDSIVerifyDataStoredInS3MNvram, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SDSIVerifyDataStoredInS3MNvram.main()
             else Framework.TEST_RESULT_FAIL)