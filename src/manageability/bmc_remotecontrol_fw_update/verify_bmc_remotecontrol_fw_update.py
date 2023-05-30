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

from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.manageability.lib.redfish_test_common import RedFishTestCommon


class VerifyBMCRemoteControlFWUpdate(RedFishTestCommon):
    """
    HPQC ID: H91691 - PI_Redfish_BMC_FWUpdate
    PHOENIX ID : 18014075210 - PI_Manageability_BMC_RemoteControl_FWUpdate_O
    This Testcase verifies the bmc firmware update using BMC Remote Control.

    Note: Please copy the BMC firmware files into the location C:\\Automation\\BKC\\Tools\\
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyBMCRemoteControlFWUpdate object.

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyBMCRemoteControlFWUpdate, self).__init__(test_log, arguments, cfg_opts)
        self.bmc_version_before_firmware_update = self.get_bmc_version()
        self.bmc_version_after_firmware_update = None

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(VerifyBMCRemoteControlFWUpdate, self).prepare()

    def execute(self):
        """
        Execute Main test case.

        Testcase flow:
        1) Check Redfish Authorizatoin .
        2) Get the current BMC version before firmware Update
        3) Update the BMC Firmware by calling uupdate service
        4) Get the BMC version after firmware Update
        5) Compare the version before and after update

        :raise:  ContentException.TestFail
        :return: True if test completed successfully, False otherwise.
        """
        ret_value = False
        if not self.check_redfish_basic_authentication():
            log_error = "Authorization of RedFish APIs failed!"
            self._log.info(log_error)
            raise content_exceptions.TestFail(log_error)

        self._log.info("Get the current BMC version before firmware Update")
        self._log.info("BMC Version before Firmware Update : {}".format(self.bmc_version_before_firmware_update))

        self._log.info("Update the BMC Firmware")
        previous_bmc_fw_path = self._common_content_configuration.get_previous_bmc_fw_file_path()
        if self.redfish_firmware_update(previous_bmc_fw_path):
            self._log.info("Successfully Updated the BMC Firmware")

        self._log.info("Get the BMC version after firmware Update")
        self.bmc_version_after_firmware_update = self.get_bmc_version()
        self._log.info("BMC Version after Firmware Update : {}".format(self.bmc_version_after_firmware_update))

        # Compare both before and after upgrade versions
        if float(self.bmc_version_before_firmware_update) != float(self.bmc_version_after_firmware_update):
            self._log.info("BMC Firmware Update from version {} to version {}".format(
                self.bmc_version_before_firmware_update, self.bmc_version_after_firmware_update))
            self.check_sel()
            return True

        log_error = "BMC firmware update verification failed"
        self._log.info(log_error)
        raise content_exceptions.TestFail(log_error)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        # Get the Current BMC filename and flash it.
        bmc_fw_path = self._common_content_configuration.get_current_bmc_fw_file_path()
        if self.redfish_firmware_update(bmc_fw_path) and self.get_bmc_version() in bmc_fw_path :
            self._log.info("Successfully Reverted the BMC Firmware to {} ".format(self.get_bmc_version()))
        bmc_version_after_revert = self.get_bmc_version()
        self._log.info("BMC Version after Firmware Update : {}".format(bmc_version_after_revert))

        # Fail the test if it is not the same.
        if float(self.bmc_version_before_firmware_update) == float(bmc_version_after_revert):
            self._log.info("BMC Firmware Update from version {} to version {}".format(
                self.bmc_version_after_firmware_update, bmc_version_after_revert))
        else:
            log_error = "BMC firmware update verification failed"
            self._log.info(log_error)
            raise content_exceptions.TestFail(log_error)
        super(VerifyBMCRemoteControlFWUpdate, self).cleanup(return_status)


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyBMCRemoteControlFWUpdate.main() else Framework.TEST_RESULT_FAIL)
