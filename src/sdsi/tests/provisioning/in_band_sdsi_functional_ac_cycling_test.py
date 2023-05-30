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

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.sdsi.tests.provisioning.sgx.sdsi_sgx_common_test import InBandSdsiSgxCommon


class SDSiFunctionalCyclingAC(InBandSdsiSgxCommon):
    """
    Glasgow_ID: 73191
    Phoenix_ID: 22012935895
    This test case verifies that a feature is not activated when license provisioning is attempted using a SDSi CAP
    license key for a feature that is not specifically supported on a processor SKU.
    Note: This test case is for use with Linux operating systems only.
    """

    AC_CYCLES = 1000

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SDSiSGXUnsupportedCap
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SDSiFunctionalCyclingAC, self).__init__(test_log, arguments, cfg_opts)

    def _query_pcie_device_status(self, deviceid: str, exp_device_presense: bool = False) -> bool:
        """
        This method is using to query the pcie device list, check the status and cross verify with expected values.

        :param deviceid: this id is passing to the lspci -s command so the command should be in bus:device.func format
        :param exp_device_presence: True means, the device should be enumerated.
        :return: raise exception if the expected values are not matching with the current status of the devices.
                 otherwise returns True
        """

        command = "lspci -s " + deviceid
        # get all coprocessor details
        dlb_pci_response = self._sdsi_obj._os.execute(command, self._sdsi_obj.cmd_timeout, "/")
        if dlb_pci_response.cmd_failed():
            self._log.error(dlb_pci_response.stderr)

        dlb_pci_information = dlb_pci_response.stdout.strip()
        self._log.debug(dlb_pci_information)
        if not exp_device_presense:
            assert dlb_pci_information == '', "{} device is present in the SUT. It is not expected in a clean SUT".format(deviceid)
        else:
            if not deviceid in dlb_pci_information:
                log_error ="{} is not present in the SUT".format(deviceid)
                self._log.error(log_error)
                raise RuntimeError(log_error)
        return True

    def verify_device_list_status(self, device_list, status: bool = False) -> None:
        """
        This method is using to check the status of the pcie device status.

        :param device_list: the device list should be in bus:device.function mode.
        :param status: expected status  means device should be present or not
        """

        for device_id in device_list:
            self._query_pcie_device_status(device_id,status)

    def prepare(self):
        # type: () -> None
        """
            Perform test preparation.
            Validate basic test requirements.
        """
        super(SDSiFunctionalCyclingAC, self).prepare()

    def execute(self):
        """Execute the test."""

        # Manual provision first

        for cycle in range(self.AC_CYCLES):
            self._log.info(f"Functional testing, reboot {cycle + 1}.")

            if not self.set_and_validate_prm_size(self.prm_size_to_apply["SG10"]):
                log_error = 'Prm max GB should increase enabling supported SGX CAP'
                self._log.error(log_error)
                raise SDSiExceptions.ProvisioningError(log_error)

            if self._sdsi_obj.get_ssku_updates_available() != 2:
                log_error = "Update counter failed to reset after reboot"
                self._log.error(log_error)
                raise SDSiExceptions.AvailableUpdatesError(log_error)

            self._log.info("Verify iax devices are enumerated with the capability payload")
            self.verify_device_list_status(['6a:02.0', '6f:02.0', '74:02.0', '79:02.0'], True)
            self.verify_device_list_status(['e7:02.0', 'ec:02.0', 'f1:02.0', 'f6:02.0'], True)
            self._log.info("Verify dsa devices are enumerated with the capability payload")
            self.verify_device_list_status(['6a:01.0', '6f:01.0', '74:01.0', '79:01.0'], True)
            self.verify_device_list_status(['e7:01.0', 'ec:01.0', 'f1:01.0', 'f6:01.0'], True)
            self._log.info("Verify dlb devices are enumerated with the capability payload")
            self.verify_device_list_status(['6d:00.0', '72:00.0', '77:00.0', '7c:00.0'], True)
            self.verify_device_list_status(['ea:00.0', 'ef:00.0', 'f4:00.0', 'f9:00.0'], True)
            self._log.info("Verify qat devices are enumerated with the capability payload")
            self.verify_device_list_status(['6b:00.0', '70:00.0', '75:00.0', '7a:00.0'], True)
            self.verify_device_list_status(['e8:00.0', 'ed:00.0', 'f2:00.0', 'f7:00.0'], True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """
            Perform Test Cleanup
        """
        super(SDSiFunctionalCyclingAC, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SDSiFunctionalCyclingAC.main()
             else Framework.TEST_RESULT_FAIL)
