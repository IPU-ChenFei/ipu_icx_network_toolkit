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
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.install_collateral import InstallCollateral
from src.sdsi.tests.provisioning.out_of_band_provisioning_test import OutOfBandProvisioningTest


class OutOfBandProvisioningTestUnderStress(OutOfBandProvisioningTest):
    """
    Glasgow_ID: 70601
    Phoenix_ID: 18014074801
    Verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate, and a capability
    activation payload and verify it is available while a stress application is running on the SUT.
    """

    CMP_LOAD_AVERAGE_BEFORE_STRESSAPP = 5
    CMP_LOAD_AVERAGE_AFTER_STRESSAPP = 20

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandProvisioningTestUnderStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self._test_log = test_log
        super(OutOfBandProvisioningTestUnderStress, self).__init__(self._test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._test_log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(OutOfBandProvisioningTestUnderStress, self).prepare()

        self._test_log.info("Clear the OS logs after the reboot.")
        self._common_content_lib.clear_dmesg_log()
        self._common_content_lib.clear_os_log()

        self._test_log.info("Read the maximum load average of the CPU prior to StressAppTest execution on SUT.")
        max_load_avg = self._sdsi_obj.get_max_load_average()
        self._test_log.info("Load average value prior to StressAppTest is {}".format(max_load_avg))
        assert max_load_avg <= self.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP, "Load average on the CPU is more than {}".format(
            self.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP)
        self._test_log.info("Load average on the CPU is less than {}".format(self.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP))

        self._test_log.info("Copy/Install a Stressful Application Test binary to SUT.")
        self._install_collateral.install_stress_test_app()

    def execute(self):
        self._test_log.info("Execute stress application on the SUT.")
        self._sdsi_obj.execute_stress_app_installer_on_sut()

        self._test_log.info("Read the maximum load average of the CPU after StressAppTest execution on SUT.")
        max_load_avg = self._sdsi_obj.get_max_load_average()
        self._test_log.info("Load average value after to StressAppTest is {}".format(max_load_avg))

        self._test_log.info(
            "Verify whether the load average is significantly increased to at least {} or greater.".format(
                self.CMP_LOAD_AVERAGE_AFTER_STRESSAPP))
        assert max_load_avg >= self.CMP_LOAD_AVERAGE_AFTER_STRESSAPP, "There is no significant increase in the CPU load after stress application."
        self._test_log.info("Load average on the CPU has increased after stress application.")

        self._test_log.info("Provision the CPU with a random payload while stress application is running on the SUT.")
        super(OutOfBandProvisioningTestUnderStress, self).execute()

        self._test_log.info("Copy the stress log to the host.")
        self.os.copy_file_from_sut_to_local("stress.log", os.path.join(self.log_dir, os.path.split("stress.log")[-1]))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(OutOfBandProvisioningTestUnderStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandProvisioningTestUnderStress.main()
             else Framework.TEST_RESULT_FAIL)
