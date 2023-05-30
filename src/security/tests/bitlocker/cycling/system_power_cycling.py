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


class BitLockerStartupTpmTest(BitLockerBaseTest):
    """Test Case ID: 18014072191"""
    BITLOCKER_KEY_TYPE = "Tpm"
    COLD_CYCLE_COUNT = 100
    WARM_CYCLE_COUNT = 100

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of BitLockerRecoveryKeyTest
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super().__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        Execute test case steps
        :return: True if Test case pass
        """
        self.enable_tpm_key()

        if self.bitlocker_key_protector_type() != self.BITLOCKER_KEY_TYPE:
            raise content_exceptions.TestFail("Tpm should be BitLocker key protector")

        if not self.restart_windows():
            raise content_exceptions.TestFail("Failed to boot into os with Tpm as BitLocker key")

        # Cold Reboots
        for cycle in range(self.COLD_CYCLE_COUNT):
            self._log.info(f"Performing cold reboot, iteration {cycle}")
            self.perform_graceful_g3()

        # Warm Reboots
        for cycle in range(self.WARM_CYCLE_COUNT):
            self._log.info(f"Performing warm reboot, iteration {cycle}")
            if not self.restart_windows():
                raise content_exceptions.TestFail(f"Failed to perform warm restart on iteration: {cycle}")

        return True

    def enable_tpm_key(self):
        """ Enable BitLocker Tpm Key Protector """
        self._log.info("Enabling BitLocker Tpm Key")
        self.run_powershell_cmd_sut(f"Add-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} -TpmProtector")
        self.run_powershell_cmd_sut(f"Resume-BitLocker -MountPoint {self._ENCRYPTED_DRIVE}")
        self._log.info(f"BitLocker key type: {self.bitlocker_key_protector_type()}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BitLockerStartupTpmTest.main() else Framework.TEST_RESULT_FAIL)
