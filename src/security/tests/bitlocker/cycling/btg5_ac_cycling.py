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
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.bitlocker.bitlocker_common import BitLockerBaseTest
from src.lib import content_exceptions


class Btg5AcCyclingTest(BitLockerBaseTest):
    """Test Case ID: 18014070837"""
    BITLOCKER_KEY_TYPE = "ExternalKey"
    BITLOCKER_KEY_LOCATION = "D:"
    COLD_CYCLE_COUNT = 250

    def prepare(self):
        """
        Pre-validating basic test requirements
        :return: None
        """
        super().prepare()

    def execute(self):
        """
        Execute test case steps
        :return: True if Test case pass
        """
        self.pc_phy.disconnect_usb(self._common_content_configuration.get_usb_set_time_delay())
        time.sleep(5.0)
        self.pc_phy.connect_usb_to_sut(self._common_content_configuration.get_usb_set_time_delay())
        time.sleep(5.0)
        self.enable_recovery_key()

        if self.bitlocker_key_protector_type() != self.BITLOCKER_KEY_TYPE:
            raise content_exceptions.TestFail("ExternalKey should be BitLocker key protector")

        for cycle in range(self.COLD_CYCLE_COUNT):
            self._log.info(f"Performing cold reboot, iteration {cycle}")
            self.perform_graceful_g3()

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self.remove_bitlocker_key()
        super(Btg5AcCyclingTest, self).cleanup(return_status)

    def enable_recovery_key(self):
        self._log.info("Enabling BitLocker recovery Key")
        self.run_powershell_cmd_sut(f"Add-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} "
                                    f"-RecoveryKeyProtector {self.BITLOCKER_KEY_LOCATION}")
        self.run_powershell_cmd_sut(f"Resume-BitLocker -MountPoint {self._ENCRYPTED_DRIVE}")
        self._log.info(f"BitLocker key type: {self.bitlocker_key_protector_type()}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Btg5AcCyclingTest.main() else Framework.TEST_RESULT_FAIL)
