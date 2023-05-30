#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :UEFI Secure Boot Interop with TDX and TXT:

    With UEFI Secure Boot enabled on the SUT, boot a TD guest successfully.
"""

import sys
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdvm.TDX050_launch_multiple_tdvm_linux import MultipleTDVMLaunch
from src.security.tests.UEFI_Secure_Boot.uefi_secure_boot_linux import LinuxUEFISecureBootTest


class TdxUefiSecureBootLinux(LinuxUEFISecureBootTest):
    """
            This recipe enables UEFI Secure Boot and TDX together and verifies a TD guest can launch with UEFI Secure
            Boot enabled in the SUT OS.

            :Scenario: Enable UEFI Secure Boot and boot to an OS.  Then launch defined number of TD guests (per
            <NUM_OF_VMS> param in content_configuration.xml).

            :Phoenix ID: 18014074013

            :Test steps:

                :1:  Install MSFT UEFI Secure Boot certificates into BIOS via the BIOS menu.

                :2:  Boot to the OS and sign the kernel with a certificate.

                :3:  Boot to BIOS again and install the certificate used to sign the kernel.

                :4:  Boot to the OS.

                :5:  Enable TDX BIOS knobs.

                :6:  Launch a TD guest.

            :Expected results: TD guest should boot and should not yield MCEs.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxUefiSecureBootLinux, self).__init__(test_log, arguments, cfg_opts)
        self.tdx = MultipleTDVMLaunch(test_log, arguments, cfg_opts)

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(TdxUefiSecureBootLinux, cls).add_arguments(parser)
        parser.add_argument("--integrity-mode", "--im", action="store", dest="INTEGRITY_MODE", default=None)

    def prepare(self) -> None:
        self.tdx.os_preparation()  # check python softlink and remaining TDX OS requirements are staged
        self._log.info("Starting UEFI Secure Boot installation.")
        super(TdxUefiSecureBootLinux, self).prepare()
        if not super(TdxUefiSecureBootLinux, self).execute():
            raise content_exceptions.TestSetupError("Failed to set up UEFI Secure Boot.")
        self.tdx.prepare()

    def execute(self) -> bool:
        return self.tdx.execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxUefiSecureBootLinux.main() else Framework.TEST_RESULT_FAIL)
