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
from src.security.tests.bitlocker.bitlocker_common import BitLockerBaseTest
from src.lib import content_exceptions


class BitLockerStartupPinTest(BitLockerBaseTest):
    BITLOCKER_PIN = 123456789
    TPM_KEY_TYPE = "TpmPin"

    def prepare(self):
        """
        Pre-validating basic test requirements
        :return: None
        """
        if not self.has_tpm():
            raise RuntimeError("This test case requires a TPM installed on the target system")
        super().prepare()

    def execute(self):
        """
        Execute test case steps
        :return: True if Test case pass
        """
        self.enable_pin_startup_requirement()

        if self.bitlocker_key_protector_type() != self.TPM_KEY_TYPE:
            raise content_exceptions.TestFail("PIN should be BitLocker key protector")

        if self.restart_windows():
            raise content_exceptions.TestFail("System booted to OS without asking for PIN protector")

        self._log.info("Writing PIN to Serial")
        self.write_to_serial(str(self.BITLOCKER_PIN))
        self._common_content_lib.wait_for_os(self.reboot_timeout)

        self.remove_bitlocker_key()
        if self.bitlocker_key_protector_type() == self.TPM_KEY_TYPE:
            raise content_exceptions.TestFail("TpmPin should no longer be BitLocker key protector")

        if not self.restart_windows():
            raise content_exceptions.TestFail("System failed to boot to OS without BitLocker key protector")

        return True

    def enable_pin_startup_requirement(self):
        """Enable startup pin bitlocker key protector"""
        self._log.info("Enabling BitLocker PIN as startup requirement")
        self.run_powershell_cmd_sut(f"Add-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} -Pin"
                                    f" ('{self.BITLOCKER_PIN}' | ConvertTo-SecureString -AsPlainText -Force) "
                                    "-TPMandPinProtector")
        self.run_powershell_cmd_sut(f"Resume-BitLocker -MountPoint {self._ENCRYPTED_DRIVE}")
        self._log.info(f"BitLocker PIN set as startup requirement: {self.BITLOCKER_PIN}")
        self._log.info(f"BitLocker key type: {self.bitlocker_key_protector_type()}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BitLockerStartupPinTest.main() else Framework.TEST_RESULT_FAIL)
