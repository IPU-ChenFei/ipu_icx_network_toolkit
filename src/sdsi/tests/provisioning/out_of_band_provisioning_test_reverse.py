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
import random
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class OutOfBandProvisioningTestReverse(ContentBaseTestCase):
    """
    Glasgow_ID: 74595
    Phoenix_ID: 22013767538
    Verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available. This test writes to sockets in varying order.
    For 2 socket systems, write socket 1 then 0. For 4 and 8 socket systems, write to sockets in a random order.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandProvisioningTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OutOfBandProvisioningTestReverse, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """Prepare the system for execution and validate basic test requirements"""
        super(OutOfBandProvisioningTestReverse, self).prepare()

        assert self._sdsi_obj.number_of_cpu >= 2, "The platform currently has only {} CPU. Please make sure to run " \
                                                  "the test on a 2+ CPU system.".format(self._sdsi_obj.number_of_cpu)

        self._sdsi_installer.verify_sdsi_installer()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify the initial failure counters for CPU_{}".format(cpu_counter + 1))
            license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(cpu_counter)
            payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(cpu_counter)

            assert license_key_auth_failures == 0, \
                "License key failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("License key authentication counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            assert payload_auth_fail_count == 0, \
                "CAP authentication failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("CAP authentication failure counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

    def execute(self):
        """
            1. Verify the license key auth fail count and payload auth fail count is 0.
            2. Get the CPU PPIN/Hardware ID of the CPU.
            3. Write the licence key certificate to the CPU. (If it is not present on the CPU)
            4. Write a random capability activation payload to the CPU. For 2 socket systems, write socket 1 then 0,
               For 4 and 8 socket systems, write to sockets in a random order.
            5. Verify the payload is available on the CPU.
            6. Verify the failure counter and max SSKU updates counter values.
        """
        read_execution_delay = 5
        payload_info = []
        socket_order = list(range(self._sdsi_obj.number_of_cpu))[::-1]
        if self._sdsi_obj.number_of_cpu > 2:
            random.shuffle(socket_order)

        for cpu_counter in socket_order:
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info("Get the SSKU updates remaining and payload failure counter for "
                           "CPU_{} before applying CAP.".format(cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            time.sleep(read_execution_delay)

            self._log.info("Get a random CAP configuration for CPU_{}.".format(cpu_counter + 1))
            current_payload_info = self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter)
            self._log.info("Apply the CAP configuration for CPU_{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_capability_activation_payload(current_payload_info, cpu_counter)
            payload_info.append(current_payload_info)
            time.sleep(read_execution_delay)

            self._log.info("Get the SSKU updates remaining and payload failure counter for "
                           "CPU_{} after applying CAP.".format(cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Verify the payload failure and ssku updates available counters are updated as "
                           "expected for CPU_{}.".format(cpu_counter + 1))
            assert payload_fail_count_before == payload_fail_count_after, \
                "Expected failure counter to be {}, but found {} for CPU_{}." \
                .format(payload_fail_count_before, payload_fail_count_after, cpu_counter + 1)
            assert max_ssku_updates_before - 1 == max_ssku_updates_after, \
                "Expecting the max available SSKU updates counter to be reduced by 1, but the values are Expected: {},"\
                " Found: {} for CPU_{}.".format(max_ssku_updates_before, max_ssku_updates_after, cpu_counter + 1)

        self.perform_graceful_g3()

        cap_index = 0
        for cpu_counter in socket_order:
            self._log.info("Verify SSKU Updates reset to max after reboot for CPU_{}.".format(cpu_counter + 1))
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            max_ssku_updates_available = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            assert ssku_updates_available == max_ssku_updates_available,\
                "Available SSKU Updates should be max for CPU_{} after cold reboot, Expected: {}, Found: {}"\
                .format(cpu_counter + 1, max_ssku_updates_available, ssku_updates_available)
            time.sleep(read_execution_delay)

            self._log.info("Verify the CAP config is available for CPU_{}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(payload_name=payload_info[cap_index][1], socket=cpu_counter), \
                "CPU_{} is not provisioned after write operation. {} CAP information is not found." \
                .format(cpu_counter + 1, payload_info[cap_index][1])
            cap_index += 1
            self._log.info("CAP config is applied successfully for CPU_{}.".format(cpu_counter + 1))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self.perform_graceful_g3()
        super(OutOfBandProvisioningTestReverse, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandProvisioningTestReverse.main()
             else Framework.TEST_RESULT_FAIL)
