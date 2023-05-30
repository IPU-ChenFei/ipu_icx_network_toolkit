# !/usr/bin/env python
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
"""
    :Linux UEFI Secure Boot testing:

    With Secure Boot enabled, boot to Linux and verify that Secure Boot is enabled.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.UEFI_Secure_Boot.uefi_secure_boot_common import LinuxUEFISecureBoot


class LinuxUEFISecureBootTest(LinuxUEFISecureBoot):
    """
            This recipe tests UEFI Secure Boot with Linux.  This test requires a USB drive connected to the SUT
            populated with the certificates used by Secure Boot which is available to BIOS for certificate installation.
            Certificates to be installed are provided in the content_configuration.xml file in the <secure_boot> tags.
            For non-PK certs, a signature GUID must be provided.

            :Scenario: Prepare OS kernel for use with Secure Boot by signing the kernel and registering the MOKs in
            shim.  Register Secure Boot certificates in the BIOS menu and enable Secure Boot.  Boot to OS and verify
            Secure Boot is enabled in the OS.

            :Phoenix IDs: 18014073306

            :Test steps:

                :1:  Sign kernel and register hash with MOK.

                :2:  Reboot SUT to complete hash installation into shim.

                :3:  Boot to BIOS menu to register Secure Boot certificates and enable Secure Boot.

                :4:  Reboot to OS and verify Secure Boot is enabled.

            :Expected results: SUT should boot without any errors.  Secure Boot should return message that it is
            enabled.

            :Reported and fixed bugs:

            :Test functions:

    """

    def execute(self) -> bool:
        return self.check_secure_boot()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LinuxUEFISecureBootTest.main() else Framework.TEST_RESULT_FAIL)
