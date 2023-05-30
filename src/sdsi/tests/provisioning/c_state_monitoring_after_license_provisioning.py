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
import os
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class CStateMonitoring(ContentBaseTestCase):
    """
    Glasgow_ID: 69435
    Phoenix_ID: 18014075447
    This test case is to verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available and monitor C-state.
    """
    BIOS_CONFIG_FILE = "c_state_knobs.cfg"
    WAIT_TIME_DELAY = 60
    GET_POWER_STATE = 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
    APPLY_POWERSAVE_MODE = 'for c in $( ls /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor ) ; do echo "powersave" > $c ; done'
    UPTIME = 'uptime'

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of CStateMonitoring

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(CStateMonitoring, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)
        self.c_state_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """preparing the setup and setting default knobs"""
        super(CStateMonitoring, self).prepare()

    def execute(self):
        """
            1. Set BIOS knobs
            2. Verify the license key auth fail count and payload auth fail count is 0.
            3. Get the CPU PPIN/Hardware ID of the CPU.
            4. Write the licence key certificate to the CPU. (If it is not present on the CPU)
            5. Write a random capability activation payload to the CPU.
            6. Verify the payload is available on the CPU.
            7. Verify the failure counter and max ssku updates counter values.
        """
        self._log.info("Set required BIOS knobs")
        self.bios_util.set_bios_knob(bios_config_file=self.c_state_bios_config_file)
        self.perform_graceful_g3()

        payload_info = self.provision_cpu()

        if self.monitor_c_state():
            raise RuntimeError("Load average is exceedeng allowed max")

        self.perform_graceful_g3()
        self.verify_provisioning(payload_info)

        return True

    def monitor_c_state(self):
        state_flag = False
        power_state = (self.os.execute(self.GET_POWER_STATE, self._command_timeout)).stdout
        if 'performance' in power_state:
            self._log.info("Platform is in Performance mode")
        self.os.execute(self.APPLY_POWERSAVE_MODE, self._command_timeout)
        power_state = (self.os.execute(self.GET_POWER_STATE, self._command_timeout)).stdout
        if 'powersave' in power_state:
            self._log.info("Platform was set to Powersave mode")

        uptime = (self.os.execute(self.UPTIME, self._command_timeout)).stdout
        load_average = re.findall(r"load average: (.*?),", uptime)

        if float(load_average[0]) < 2.0:
            self._log.info("Load average is " + str(load_average[0]))
            state_flag = True

    def provision_cpu(self):
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU{}.".format(cpu_counter))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU{} before applying CAP.".format(
                    cpu_counter))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Get a random CAP configuration for CPU{}.".format(cpu_counter))
            payload_info = self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter)

            self._log.info("Apply the CAP configuration for CPU{}.".format(cpu_counter))
            self._sdsi_obj.apply_capability_activation_payload(payload_info, cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU{} after applying CAP.".format(
                    cpu_counter))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info(
                "Verify the payload failure and ssku updates available counters are updated as expected for CPU{}.".format(
                    cpu_counter))
            assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU {}.".format(
                payload_fail_count_before, payload_fail_count_after, cpu_counter)
            assert max_ssku_updates_before - 1 == max_ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU {}.".format(
                max_ssku_updates_before, max_ssku_updates_after, cpu_counter)

        self._log.info("")
        # self.perform_graceful_g3()
        return payload_info

    def verify_provisioning(self, payload_info):
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            max_ssku_updates_available = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            assert ssku_updates_available == max_ssku_updates_available, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU {}.".format(
                ssku_updates_available, max_ssku_updates_available, cpu_counter)

            self._log.info("Verify the CAP config is available for CPU{}.".format(cpu_counter))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_info[1],
                socket=cpu_counter), "CPU{} is not provisioned after write operation. {} CAP information is not found.".format(
                cpu_counter, payload_info[1])

            self._log.info("CAP config is applied successfully for CPU{}.".format(cpu_counter))

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(CStateMonitoring, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CStateMonitoring.main()
             else Framework.TEST_RESULT_FAIL)
