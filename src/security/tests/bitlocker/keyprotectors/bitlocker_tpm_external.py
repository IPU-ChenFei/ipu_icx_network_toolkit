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


class BitLockerTpmExternalKeyTest(BitLockerBaseTest):
    """Test Case ID: 18014073223"""
    INTEROP_KNOBS = "collateral/interop_knobs.cfg"
    BITLOCKER_KEY_TYPE = "Tpm\nExternalKey"
    BITLOCKER_KEY_LOCATION = "D:"
    USB_DETECT_DELAY = 5
    BOOT_FAIL_TIMEOUT = 20

    def execute(self):
        """
        Execute test case steps
        :return: True if Test case pass
        """
        self.pc_phy.disconnect_usb(self._common_content_configuration.get_usb_set_time_delay())
        time.sleep(self.USB_DETECT_DELAY)
        self.pc_phy.connect_usb_to_sut(self._common_content_configuration.get_usb_set_time_delay())
        time.sleep(self.USB_DETECT_DELAY)

        self.enable_tpm_key()
        self.enable_external_key()

        if self.bitlocker_key_protector_type() != self.BITLOCKER_KEY_TYPE:
            raise content_exceptions.TestFail("TpmExternalKey should be BitLocker key protector")

        self.pc_phy.disconnect_usb(self._common_content_configuration.get_usb_set_time_delay())

        if self.restart_windows():
            raise content_exceptions.TestFail("System booted without usb key")
        self._log.info("System did not boot without usb key as expected")

        self.pc_phy.connect_usb_to_sut(self._common_content_configuration.get_usb_set_time_delay())
        self.perform_graceful_g3()
        self._log.info("System booted to os after usb key connected")

        return True

    def enable_external_key(self):
        """
        Enable BitLocker External Key Protector
        """
        self._log.info("Enabling BitLocker external Key")
        self.run_powershell_cmd_sut(f"Add-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} "
                                    "-RecoveryKeyProtector {self.BITLOCKER_KEY_LOCATION}")
        self.run_powershell_cmd_sut("Resume-BitLocker -MountPoint {self._ENCRYPTED_DRIVE}")
        self._log.info(f"BitLocker key type: {self.bitlocker_key_protector_type()}")

    def enable_tpm_key(self):
        """ Enable BitLocker Tpm Key Protector """
        self._log.info("Enabling BitLocker Tpm Key")
        self.run_powershell_cmd_sut(f"Add-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} -TpmProtector")
        self.run_powershell_cmd_sut("Resume-BitLocker -MountPoint {self._ENCRYPTED_DRIVE}")
        self._log.info(f"BitLocker key type: {self.bitlocker_key_protector_type()}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BitLockerTpmExternalKeyTest.main() else Framework.TEST_RESULT_FAIL)
