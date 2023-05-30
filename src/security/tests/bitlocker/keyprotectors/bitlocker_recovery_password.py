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
import os
import sys
from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.bitlocker.bitlocker_common import BitLockerBaseTest
from src.lib import content_exceptions


class BitLockerRecoveryPasswordTest(BitLockerBaseTest):
    """Test Case ID: 18014072331"""
    BITLOCKER_KEY_TYPE = "RecoveryPassword"
    BITLOCKER_RECOVERY_PASSWORD = os.getenv('bitlocker_recovery_password')

    def prepare(self):
        """
        Pre-validating basic test requirements
        :return: None
        """
        super(BitLockerRecoveryPasswordTest, self).prepare()

    def execute(self):
        """
        Execute test case steps
        :return: True if Test case pass
        """
        if not self.BITLOCKER_RECOVERY_PASSWORD:
            raise content_exceptions.TestFail("No password found for environment variable bitlocker_recovery_password."
                                              "Format: 111111-111111-111111-111111-111111-111111-111111-111111")

        self.enable_recovery_password()

        if self.bitlocker_key_protector_type() != self.BITLOCKER_KEY_TYPE:
            raise content_exceptions.TestFail("RecoveryPassword should be BitLocker key protector")

        if self.restart_windows():
            raise content_exceptions.TestFail("BitLocker should have locked")

        self._log.info(f"Writing Recovery Password to Serial: {self.BITLOCKER_RECOVERY_PASSWORD.replace('-', '')}")
        self.write_to_serial(self.BITLOCKER_RECOVERY_PASSWORD.replace('-', ''))
        self._common_content_lib.wait_for_os(self.reboot_timeout)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(BitLockerRecoveryPasswordTest, self).cleanup(return_status)

    def enable_recovery_password(self):
        self._log.info("Enabling BitLocker Recovery Password")
        self.run_powershell_cmd_sut(f"Add-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} "
                                    f"-RecoveryPasswordProtector "
                                    f"-RecoveryPassword '{self.BITLOCKER_RECOVERY_PASSWORD}'")
        self.run_powershell_cmd_sut(f"Resume-BitLocker -MountPoint {self._ENCRYPTED_DRIVE}")
        self._log.info(f"BitLocker Recovery Password set as startup requirement: {self.BITLOCKER_RECOVERY_PASSWORD}")
        self._log.info(f"BitLocker key type: {self.bitlocker_key_protector_type()}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BitLockerRecoveryPasswordTest.main() else Framework.TEST_RESULT_FAIL)
